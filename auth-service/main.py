"""
Authentication Service für LLM-Frontend
Vollständige JWT-basierte Authentifizierung mit User Management
"""
from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import Optional
import os
import sys
import time
from datetime import datetime, timedelta

# Pfad-Setup für Imports
sys.path.append('/app')
sys.path.append('/app/backend-core')
sys.path.append('/app/backend-core/models')
sys.path.append('/app/backend-core/utils')

# Lokale Imports
from logging_config import setup_logging, get_auth_logger
from models.schemas import *
from models.database import User, Role, UserRole, ApiKey, Token, UserBalance, Base
from utils.auth import (
    authenticate_user, get_password_hash, create_access_token, create_refresh_token,
    verify_token, get_user_by_email, get_user_by_username, get_user_by_id,
    create_email_verification_token, verify_email_token, create_password_reset_token,
    reset_password, revoke_token, revoke_all_user_tokens, cleanup_expired_tokens,
    hash_token, is_token_revoked
)

# Logging konfigurieren
setup_logging("auth-service")
logger = get_auth_logger()

# FastAPI App
app = FastAPI(
    title="LLM-Frontend Authentication Service",
    description="JWT-basierte Authentifizierung mit User Management",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In Produktion einschränken
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals für Tracking
startup_time = time.time()

# ===================================================
# DATABASE SETUP
# ===================================================

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@postgres-db:5432/llm_frontend_db"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database():
    """Database dependency"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

# ===================================================
# SECURITY DEPENDENCIES
# ===================================================

security = HTTPBearer(auto_error=False)

def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """
    Holt den aktuellen Benutzer aus dem JWT Token
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = credentials.credentials
    
    # Token validieren
    payload = verify_token(token, "access")
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Prüfen ob Token widerrufen wurde
    if is_token_revoked(db, token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = get_user_by_id(db, int(user_id))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return user

def get_current_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """
    Stellt sicher, dass der aktuelle Benutzer Admin-Rechte hat
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

# ===================================================
# STARTUP/SHUTDOWN EVENTS
# ===================================================

@app.on_event("startup")
async def startup_event():
    """Service-Start-Events"""
    logger.info("Authentication Service starting up")
    
    # Datenbank-Verbindung testen
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection successful")
    except Exception as e:
        logger.error("Database connection failed", error=str(e))
        raise
    
    # Abgelaufene Tokens aufräumen
    db = SessionLocal()
    try:
        cleaned_count = cleanup_expired_tokens(db)
        logger.info("Startup cleanup completed", expired_tokens_removed=cleaned_count)
    except Exception as e:
        logger.error("Startup cleanup failed", error=str(e))
    finally:
        db.close()

@app.on_event("shutdown")
async def shutdown_event():
    """Service-Shutdown-Events"""
    logger.info("Authentication Service shutting down")

# ===================================================
# HEALTH CHECK ENDPOINTS
# ===================================================

@app.get("/", response_model=MessageResponse)
def read_root():
    """Root endpoint"""
    logger.info("Root endpoint accessed")
    return MessageResponse(
        message="LLM-Frontend Authentication Service",
        detail="JWT-basierte Authentifizierung ist aktiv"
    )

@app.get("/health", response_model=HealthResponse)
def health_check():
    """Detaillierter Health Check"""
    logger.debug("Health check endpoint accessed")
    
    # Datenbank-Verbindung testen
    database_healthy = False
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        database_healthy = True
    except Exception as e:
        logger.error("Health check database test failed", error=str(e))
    
    uptime = time.time() - startup_time
    
    return HealthResponse(
        status="healthy" if database_healthy else "degraded",
        service="auth-service",
        timestamp=datetime.utcnow(),
        database=database_healthy,
        uptime=uptime
    )

# ===================================================
# AUTHENTICATION ENDPOINTS
# ===================================================

@app.post("/register", response_model=SuccessResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, db: Session = Depends(get_database)):
    """
    Neuen Benutzer registrieren
    """
    logger.info("User registration attempt", email=user_data.email, username=user_data.username)
    
    # Prüfen ob E-Mail bereits existiert
    if get_user_by_email(db, user_data.email):
        logger.warning("Registration failed - email exists", email=user_data.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Prüfen ob Username bereits existiert
    if get_user_by_username(db, user_data.username):
        logger.warning("Registration failed - username exists", username=user_data.username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    try:
        # Neuen Benutzer erstellen
        hashed_password = get_password_hash(user_data.password)
        
        db_user = User(
            email=user_data.email,
            username=user_data.username,
            full_name=user_data.full_name,
            password_hash=hashed_password,
            is_active=True,
            email_verified=False
        )
        
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        
        # Standard-Rolle zuweisen
        user_role = db.query(Role).filter(Role.name == "user").first()
        if user_role:
            db_user_role = UserRole(user_id=db_user.id, role_id=user_role.id)
            db.add(db_user_role)
        
        # Benutzer-Guthaben initialisieren
        user_balance = UserBalance(user_id=db_user.id, balance=0.00)
        db.add(user_balance)
        
        db.commit()
        
        # E-Mail-Verifizierungs-Token erstellen
        verification_token = create_email_verification_token(db, db_user.id)
        
        logger.info("User registered successfully", 
                   user_id=db_user.id, 
                   email=user_data.email,
                   username=user_data.username)
        
        return SuccessResponse(
            success=True,
            message="User registered successfully",
            data={
                "user_id": db_user.id,
                "email_verification_required": True,
                "verification_token": verification_token  # In Produktion per E-Mail senden
            }
        )
    
    except Exception as e:
        logger.error("User registration failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@app.post("/login", response_model=TokenResponse)
def login_user(user_credentials: UserLogin, db: Session = Depends(get_database)):
    """
    Benutzer anmelden und JWT Tokens zurückgeben
    """
    logger.info("Login attempt", email=user_credentials.email)
    
    # Benutzer authentifizieren
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        logger.warning("Login failed - invalid credentials", email=user_credentials.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    try:
        # JWT Tokens erstellen
        access_token_expires = timedelta(minutes=15)
        refresh_token_expires = timedelta(days=30)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "username": user.username},
            expires_delta=access_token_expires
        )
        
        refresh_token = create_refresh_token(
            data={"sub": str(user.id)},
            expires_delta=refresh_token_expires
        )
        
        logger.info("Login successful", user_id=user.id, email=user.email)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    
    except Exception as e:
        logger.error("Token creation failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@app.post("/refresh", response_model=TokenResponse)
def refresh_token(token_data: TokenRefresh, db: Session = Depends(get_database)):
    """
    Refresh Token verwenden um neuen Access Token zu erhalten
    """
    logger.debug("Token refresh attempt")
    
    # Refresh Token validieren
    payload = verify_token(token_data.refresh_token, "refresh")
    if not payload:
        logger.warning("Token refresh failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    # Prüfen ob Token widerrufen wurde
    if is_token_revoked(db, token_data.refresh_token):
        logger.warning("Token refresh failed - token revoked")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token has been revoked"
        )
    
    user_id = payload.get("sub")
    user = get_user_by_id(db, int(user_id))
    if not user:
        logger.warning("Token refresh failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    try:
        # Neuen Access Token erstellen
        access_token_expires = timedelta(minutes=15)
        
        access_token = create_access_token(
            data={"sub": str(user.id), "email": user.email, "username": user.username},
            expires_delta=access_token_expires
        )
        
        logger.debug("Token refresh successful", user_id=user.id)
        
        return TokenResponse(
            access_token=access_token,
            refresh_token=token_data.refresh_token,  # Gleicher Refresh Token
            token_type="bearer",
            expires_in=int(access_token_expires.total_seconds())
        )
    
    except Exception as e:
        logger.error("Token refresh failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@app.post("/logout", response_model=MessageResponse)
def logout_user(
    token_data: TokenRevoke,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Benutzer abmelden und Token widerrufen
    """
    logger.info("Logout attempt", user_id=current_user.id)
    
    try:
        # Token widerrufen
        revoked = revoke_token(db, token_data.token)
        if not revoked:
            logger.warning("Logout - token not found", user_id=current_user.id)
        
        logger.info("Logout successful", user_id=current_user.id)
        
        return MessageResponse(
            message="Logged out successfully",
            detail="Token has been revoked"
        )
    
    except Exception as e:
        logger.error("Logout failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@app.post("/logout-all", response_model=MessageResponse)
def logout_all_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Von allen Geräten abmelden (alle Tokens widerrufen)
    """
    logger.info("Logout all devices", user_id=current_user.id)
    
    try:
        # Alle Access- und Refresh-Tokens widerrufen
        access_count = revoke_all_user_tokens(db, current_user.id, "access")
        refresh_count = revoke_all_user_tokens(db, current_user.id, "refresh")
        
        logger.info("Logout all successful", 
                   user_id=current_user.id,
                   access_tokens_revoked=access_count,
                   refresh_tokens_revoked=refresh_count)
        
        return MessageResponse(
            message="Logged out from all devices",
            detail=f"Revoked {access_count + refresh_count} tokens"
        )
    
    except Exception as e:
        logger.error("Logout all failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# ===================================================
# USER MANAGEMENT ENDPOINTS
# ===================================================

@app.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Aktuelle Benutzerinformationen abrufen
    """
    logger.debug("User info requested", user_id=current_user.id)
    return UserResponse.from_orm(current_user)

@app.put("/me", response_model=UserResponse)
def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Aktuelle Benutzerinformationen aktualisieren
    """
    logger.info("User update attempt", user_id=current_user.id)
    
    try:
        # Felder aktualisieren
        if user_update.full_name is not None:
            current_user.full_name = user_update.full_name
        
        if user_update.email is not None:
            # Prüfen ob neue E-Mail bereits existiert
            existing_user = get_user_by_email(db, user_update.email)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Email already in use"
                )
            current_user.email = user_update.email
            current_user.email_verified = False  # Erneute Verifizierung erforderlich
        
        if user_update.username is not None:
            # Prüfen ob neuer Username bereits existiert
            existing_user = get_user_by_username(db, user_update.username)
            if existing_user and existing_user.id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
            current_user.username = user_update.username
        
        db.commit()
        db.refresh(current_user)
        
        logger.info("User updated successfully", user_id=current_user.id)
        return UserResponse.from_orm(current_user)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("User update failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Update failed"
        )

# ===================================================
# PASSWORD MANAGEMENT ENDPOINTS
# ===================================================

@app.post("/change-password", response_model=MessageResponse)
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database)
):
    """
    Passwort ändern (authentifizierter Benutzer)
    """
    logger.info("Password change attempt", user_id=current_user.id)
    
    # Aktuelles Passwort verifizieren
    if not authenticate_user(db, current_user.email, password_data.current_password):
        logger.warning("Password change failed - invalid current password", user_id=current_user.id)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid current password"
        )
    
    try:
        # Neues Passwort setzen
        current_user.password_hash = get_password_hash(password_data.new_password)
        db.commit()
        
        # Alle Tokens widerrufen (Sicherheit)
        revoke_all_user_tokens(db, current_user.id, "access")
        revoke_all_user_tokens(db, current_user.id, "refresh")
        
        logger.info("Password changed successfully", user_id=current_user.id)
        
        return MessageResponse(
            message="Password changed successfully",
            detail="Please log in again with your new password"
        )
    
    except Exception as e:
        logger.error("Password change failed", error=str(e))
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )

@app.post("/request-password-reset", response_model=MessageResponse)
def request_password_reset(
    reset_request: PasswordResetRequest,
    db: Session = Depends(get_database)
):
    """
    Passwort-Reset anfordern
    """
    logger.info("Password reset request", email=reset_request.email)
    
    user = get_user_by_email(db, reset_request.email)
    if not user:
        # Sicherheit: Immer Success zurückgeben, auch wenn Benutzer nicht existiert
        logger.warning("Password reset request for non-existent email", email=reset_request.email)
        return MessageResponse(
            message="Password reset email sent",
            detail="If the email exists, you will receive a reset link"
        )
    
    try:
        # Reset-Token erstellen
        reset_token = create_password_reset_token(db, user.id)
        
        logger.info("Password reset token created", user_id=user.id)
        
        return MessageResponse(
            message="Password reset email sent",
            detail=f"Reset token: {reset_token}"  # In Produktion per E-Mail senden
        )
    
    except Exception as e:
        logger.error("Password reset request failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset request failed"
        )

@app.post("/reset-password", response_model=MessageResponse)
def reset_user_password(
    reset_data: PasswordReset,
    db: Session = Depends(get_database)
):
    """
    Passwort mit Reset-Token zurücksetzen
    """
    logger.info("Password reset attempt")
    
    try:
        success = reset_password(db, reset_data.token, reset_data.new_password)
        if not success:
            logger.warning("Password reset failed - invalid token")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        logger.info("Password reset successful")
        
        return MessageResponse(
            message="Password reset successfully",
            detail="Please log in with your new password"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Password reset failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

# ===================================================
# EMAIL VERIFICATION ENDPOINTS
# ===================================================

@app.post("/verify-email", response_model=MessageResponse)
def verify_user_email(
    verification: EmailVerification,
    db: Session = Depends(get_database)
):
    """
    E-Mail-Adresse verifizieren
    """
    logger.info("Email verification attempt")
    
    user = verify_email_token(db, verification.token)
    if not user:
        logger.warning("Email verification failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    logger.info("Email verified successfully", user_id=user.id)
    
    return MessageResponse(
        message="Email verified successfully",
        detail="Your email address has been confirmed"
    )

@app.post("/resend-verification", response_model=MessageResponse)
def resend_verification_email(
    verification_request: EmailVerificationRequest,
    db: Session = Depends(get_database)
):
    """
    Verifizierungs-E-Mail erneut senden
    """
    logger.info("Resend verification request", email=verification_request.email)
    
    user = get_user_by_email(db, verification_request.email)
    if not user:
        # Sicherheit: Immer Success zurückgeben
        return MessageResponse(
            message="Verification email sent",
            detail="If the email exists and is unverified, a new verification link was sent"
        )
    
    if user.email_verified:
        return MessageResponse(
            message="Email already verified",
            detail="This email address is already verified"
        )
    
    try:
        # Neuen Verifizierungs-Token erstellen
        verification_token = create_email_verification_token(db, user.id)
        
        logger.info("Verification email resent", user_id=user.id)
        
        return MessageResponse(
            message="Verification email sent",
            detail=f"Verification token: {verification_token}"  # In Produktion per E-Mail senden
        )
    
    except Exception as e:
        logger.error("Resend verification failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send verification email"
        )

# ===================================================
# ADMIN ENDPOINTS
# ===================================================

@app.get("/admin/cleanup-tokens", response_model=MessageResponse)
def admin_cleanup_tokens(
    admin_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_database)
):
    """
    Abgelaufene Tokens aufräumen (Admin)
    """
    logger.info("Admin token cleanup", admin_id=admin_user.id)
    
    try:
        cleaned_count = cleanup_expired_tokens(db)
        
        logger.info("Admin token cleanup completed", 
                   admin_id=admin_user.id,
                   tokens_cleaned=cleaned_count)
        
        return MessageResponse(
            message="Token cleanup completed",
            detail=f"Removed {cleaned_count} expired tokens"
        )
    
    except Exception as e:
        logger.error("Admin token cleanup failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token cleanup failed"
        )

# ===================================================
# ERROR HANDLERS
# ===================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP Exception Handler mit Logging"""
    logger.warning("HTTP Exception", 
                  status_code=exc.status_code, 
                  detail=exc.detail,
                  path=request.url.path)
    
    return ErrorResponse(
        error=exc.detail,
        code=str(exc.status_code)
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)