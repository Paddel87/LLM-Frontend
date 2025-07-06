"""
Authentication Utilities für LLM-Frontend
"""
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import os
import secrets
import hashlib
from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
from sqlalchemy.orm import Session
from models.database import User, Token, TokenType
import structlog

logger = structlog.get_logger(__name__)

# Konfiguration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-jwt-secret-key")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "30"))

# Password Context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# ===================================================
# PASSWORD HANDLING
# ===================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifiziert ein Passwort gegen den Hash
    """
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as e:
        logger.error("Password verification failed", error=str(e))
        return False

def get_password_hash(password: str) -> str:
    """
    Erstellt einen Hash für ein Passwort
    """
    return pwd_context.hash(password)

def generate_secure_token(length: int = 32) -> str:
    """
    Generiert einen sicheren Token
    """
    return secrets.token_urlsafe(length)

def hash_token(token: str) -> str:
    """
    Hasht einen Token für die Speicherung
    """
    return hashlib.sha256(token.encode()).hexdigest()

# ===================================================
# JWT TOKEN HANDLING
# ===================================================

def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Erstellt einen JWT Access Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire, "type": "access"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.debug("Access token created", 
                user_id=data.get("sub"), 
                expires=expire.isoformat())
    
    return encoded_jwt

def create_refresh_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """
    Erstellt einen JWT Refresh Token
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    
    to_encode.update({"exp": expire, "type": "refresh"})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    
    logger.debug("Refresh token created", 
                user_id=data.get("sub"), 
                expires=expire.isoformat())
    
    return encoded_jwt

def verify_token(token: str, token_type: str = "access") -> Optional[Dict[str, Any]]:
    """
    Verifiziert einen JWT Token
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        
        # Token-Typ prüfen
        if payload.get("type") != token_type:
            logger.warning("Invalid token type", 
                         expected=token_type, 
                         actual=payload.get("type"))
            return None
        
        # Ablaufzeit prüfen
        exp = payload.get("exp")
        if exp is None:
            logger.warning("Token has no expiration")
            return None
        
        if datetime.utcnow() > datetime.utcfromtimestamp(exp):
            logger.warning("Token expired", expired_at=exp)
            return None
        
        return payload
    
    except JWTError as e:
        logger.error("JWT verification failed", error=str(e))
        return None
    except Exception as e:
        logger.error("Token verification failed", error=str(e))
        return None

def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Dekodiert einen Token ohne Verifikation (für Debug)
    """
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except Exception as e:
        logger.error("Token decoding failed", error=str(e))
        return None

# ===================================================
# DATABASE TOKEN MANAGEMENT
# ===================================================

def store_token_in_db(db: Session, user_id: int, token: str, token_type: str, expires_at: datetime) -> Token:
    """
    Speichert einen Token in der Datenbank
    """
    token_hash = hash_token(token)
    
    db_token = Token(
        user_id=user_id,
        token_hash=token_hash,
        token_type=token_type,
        expires_at=expires_at
    )
    
    db.add(db_token)
    db.commit()
    db.refresh(db_token)
    
    logger.debug("Token stored in database", 
                token_id=db_token.id, 
                user_id=user_id, 
                token_type=token_type)
    
    return db_token

def revoke_token(db: Session, token: str) -> bool:
    """
    Widerruft einen Token
    """
    try:
        token_hash = hash_token(token)
        db_token = db.query(Token).filter(
            Token.token_hash == token_hash,
            Token.is_revoked == False
        ).first()
        
        if db_token:
            db_token.is_revoked = True
            db.commit()
            logger.info("Token revoked", token_id=db_token.id)
            return True
        
        logger.warning("Token not found for revocation")
        return False
    
    except Exception as e:
        logger.error("Token revocation failed", error=str(e))
        return False

def revoke_all_user_tokens(db: Session, user_id: int, token_type: Optional[str] = None) -> int:
    """
    Widerruft alle Tokens eines Benutzers
    """
    try:
        query = db.query(Token).filter(
            Token.user_id == user_id,
            Token.is_revoked == False
        )
        
        if token_type:
            query = query.filter(Token.token_type == token_type)
        
        tokens = query.all()
        count = len(tokens)
        
        for token in tokens:
            token.is_revoked = True
        
        db.commit()
        logger.info("User tokens revoked", user_id=user_id, count=count, token_type=token_type)
        return count
    
    except Exception as e:
        logger.error("Token revocation failed", error=str(e))
        return 0

def is_token_revoked(db: Session, token: str) -> bool:
    """
    Prüft, ob ein Token widerrufen wurde
    """
    try:
        token_hash = hash_token(token)
        db_token = db.query(Token).filter(
            Token.token_hash == token_hash
        ).first()
        
        if not db_token:
            return True  # Token nicht gefunden = als widerrufen betrachten
        
        return db_token.is_revoked
    
    except Exception as e:
        logger.error("Token revocation check failed", error=str(e))
        return True

def cleanup_expired_tokens(db: Session) -> int:
    """
    Entfernt abgelaufene Tokens aus der Datenbank
    """
    try:
        expired_tokens = db.query(Token).filter(
            Token.expires_at < datetime.utcnow()
        ).all()
        
        count = len(expired_tokens)
        
        for token in expired_tokens:
            db.delete(token)
        
        db.commit()
        logger.info("Expired tokens cleaned up", count=count)
        return count
    
    except Exception as e:
        logger.error("Token cleanup failed", error=str(e))
        return 0

# ===================================================
# USER AUTHENTICATION
# ===================================================

def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """
    Authentifiziert einen Benutzer
    """
    try:
        user = db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
        
        if not user:
            logger.warning("User not found or inactive", email=email)
            return None
        
        if not verify_password(password, user.password_hash):
            logger.warning("Invalid password", email=email)
            return None
        
        # Last login aktualisieren
        user.last_login = datetime.utcnow()
        db.commit()
        
        logger.info("User authenticated successfully", user_id=user.id, email=email)
        return user
    
    except Exception as e:
        logger.error("User authentication failed", error=str(e))
        return None

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """
    Holt einen Benutzer anhand der ID
    """
    try:
        return db.query(User).filter(
            User.id == user_id,
            User.is_active == True
        ).first()
    except Exception as e:
        logger.error("User lookup failed", error=str(e))
        return None

def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """
    Holt einen Benutzer anhand der E-Mail
    """
    try:
        return db.query(User).filter(
            User.email == email,
            User.is_active == True
        ).first()
    except Exception as e:
        logger.error("User lookup failed", error=str(e))
        return None

def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """
    Holt einen Benutzer anhand des Benutzernamens
    """
    try:
        return db.query(User).filter(
            User.username == username,
            User.is_active == True
        ).first()
    except Exception as e:
        logger.error("User lookup failed", error=str(e))
        return None

# ===================================================
# EMAIL VERIFICATION & PASSWORD RESET
# ===================================================

def create_email_verification_token(db: Session, user_id: int) -> str:
    """
    Erstellt einen E-Mail-Verifizierungs-Token
    """
    token = generate_secure_token(32)
    expires_at = datetime.utcnow() + timedelta(hours=24)
    
    # Token in Datenbank speichern
    store_token_in_db(db, user_id, token, TokenType.EMAIL_VERIFICATION.value, expires_at)
    
    # Token auch im User-Objekt speichern (für einfacheren Zugriff)
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.email_verification_token = hash_token(token)
        db.commit()
    
    logger.info("Email verification token created", user_id=user_id)
    return token

def verify_email_token(db: Session, token: str) -> Optional[User]:
    """
    Verifiziert einen E-Mail-Verifizierungs-Token
    """
    try:
        token_hash = hash_token(token)
        
        # Token in Datenbank finden
        db_token = db.query(Token).filter(
            Token.token_hash == token_hash,
            Token.token_type == TokenType.EMAIL_VERIFICATION.value,
            Token.is_revoked == False,
            Token.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            logger.warning("Email verification token not found or expired")
            return None
        
        # Benutzer finden
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user:
            logger.error("User not found for email verification token")
            return None
        
        # E-Mail als verifiziert markieren
        user.email_verified = True
        user.email_verification_token = None
        
        # Token widerrufen
        db_token.is_revoked = True
        
        db.commit()
        logger.info("Email verified successfully", user_id=user.id)
        return user
    
    except Exception as e:
        logger.error("Email verification failed", error=str(e))
        return None

def create_password_reset_token(db: Session, user_id: int) -> str:
    """
    Erstellt einen Passwort-Reset-Token
    """
    token = generate_secure_token(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    # Token in Datenbank speichern
    store_token_in_db(db, user_id, token, TokenType.PASSWORD_RESET.value, expires_at)
    
    # Token auch im User-Objekt speichern
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        user.password_reset_token = hash_token(token)
        user.password_reset_expires = expires_at
        db.commit()
    
    logger.info("Password reset token created", user_id=user_id)
    return token

def verify_password_reset_token(db: Session, token: str) -> Optional[User]:
    """
    Verifiziert einen Passwort-Reset-Token
    """
    try:
        token_hash = hash_token(token)
        
        # Token in Datenbank finden
        db_token = db.query(Token).filter(
            Token.token_hash == token_hash,
            Token.token_type == TokenType.PASSWORD_RESET.value,
            Token.is_revoked == False,
            Token.expires_at > datetime.utcnow()
        ).first()
        
        if not db_token:
            logger.warning("Password reset token not found or expired")
            return None
        
        # Benutzer finden
        user = db.query(User).filter(User.id == db_token.user_id).first()
        if not user:
            logger.error("User not found for password reset token")
            return None
        
        logger.info("Password reset token verified", user_id=user.id)
        return user
    
    except Exception as e:
        logger.error("Password reset verification failed", error=str(e))
        return None

def reset_password(db: Session, token: str, new_password: str) -> bool:
    """
    Setzt ein Passwort mit einem Reset-Token zurück
    """
    try:
        user = verify_password_reset_token(db, token)
        if not user:
            return False
        
        # Neues Passwort setzen
        user.password_hash = get_password_hash(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        
        # Token widerrufen
        token_hash = hash_token(token)
        db_token = db.query(Token).filter(
            Token.token_hash == token_hash,
            Token.token_type == TokenType.PASSWORD_RESET.value
        ).first()
        
        if db_token:
            db_token.is_revoked = True
        
        # Alle Access- und Refresh-Tokens des Benutzers widerrufen
        revoke_all_user_tokens(db, user.id, TokenType.ACCESS.value)
        revoke_all_user_tokens(db, user.id, TokenType.REFRESH.value)
        
        db.commit()
        logger.info("Password reset successfully", user_id=user.id)
        return True
    
    except Exception as e:
        logger.error("Password reset failed", error=str(e))
        return False 