"""
Pydantic Schemas für Authentication Service
"""
from pydantic import BaseModel, EmailStr, validator
from typing import Optional, List
from datetime import datetime

# ===================================================
# USER SCHEMAS
# ===================================================

class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str
    
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(UserBase):
    id: int
    is_active: bool
    is_admin: bool
    email_verified: bool
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    
    @validator('username')
    def validate_username(cls, v):
        if v is not None and len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if v is not None and not v.isalnum():
            raise ValueError('Username must contain only alphanumeric characters')
        return v

# ===================================================
# TOKEN SCHEMAS
# ===================================================

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int

class TokenRefresh(BaseModel):
    refresh_token: str

class TokenRevoke(BaseModel):
    token: str

# ===================================================
# PASSWORD SCHEMAS
# ===================================================

class PasswordChange(BaseModel):
    current_password: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('New password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('New password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('New password must contain at least one digit')
        return v

class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str
    
    @validator('new_password')
    def validate_new_password(cls, v):
        if len(v) < 8:
            raise ValueError('New password must be at least 8 characters long')
        if not any(c.isupper() for c in v):
            raise ValueError('New password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('New password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('New password must contain at least one digit')
        return v

# ===================================================
# EMAIL VERIFICATION SCHEMAS
# ===================================================

class EmailVerificationRequest(BaseModel):
    email: EmailStr

class EmailVerification(BaseModel):
    token: str

# ===================================================
# ROLE SCHEMAS
# ===================================================

class RoleBase(BaseModel):
    name: str
    description: Optional[str] = None

class RoleCreate(RoleBase):
    pass

class RoleResponse(RoleBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserRoleAssignment(BaseModel):
    user_id: int
    role_id: int

# ===================================================
# PERMISSION SCHEMAS
# ===================================================

class PermissionBase(BaseModel):
    name: str
    resource: str
    action: str
    description: Optional[str] = None

class PermissionCreate(PermissionBase):
    pass

class PermissionResponse(PermissionBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class RolePermissionAssignment(BaseModel):
    role_id: int
    permission_id: int

# ===================================================
# API KEY SCHEMAS
# ===================================================

class ApiKeyBase(BaseModel):
    provider: str
    key_name: str

class ApiKeyCreate(ApiKeyBase):
    api_key: str  # Wird verschlüsselt gespeichert

class ApiKeyResponse(ApiKeyBase):
    id: int
    is_active: bool
    created_at: datetime
    last_used: Optional[datetime] = None
    
    class Config:
        from_attributes = True

class ApiKeyUpdate(BaseModel):
    key_name: Optional[str] = None
    is_active: Optional[bool] = None

# ===================================================
# RESPONSE SCHEMAS
# ===================================================

class MessageResponse(BaseModel):
    message: str
    detail: Optional[str] = None

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    code: Optional[str] = None

class SuccessResponse(BaseModel):
    success: bool
    message: str
    data: Optional[dict] = None

# ===================================================
# HEALTH CHECK SCHEMAS
# ===================================================

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime
    database: bool
    uptime: Optional[float] = None

# ===================================================
# PAGINATION SCHEMAS
# ===================================================

class PaginationParams(BaseModel):
    page: int = 1
    size: int = 10
    
    @validator('page')
    def validate_page(cls, v):
        if v < 1:
            raise ValueError('Page must be >= 1')
        return v
    
    @validator('size')
    def validate_size(cls, v):
        if v < 1:
            raise ValueError('Size must be >= 1')
        if v > 100:
            raise ValueError('Size must be <= 100')
        return v

class PaginatedResponse(BaseModel):
    items: List[dict]
    total: int
    page: int
    size: int
    pages: int 