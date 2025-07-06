"""
SQLAlchemy Modelle für LLM-Frontend
"""
from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DECIMAL, TIMESTAMP, 
    ForeignKey, UniqueConstraint, Index, CheckConstraint, func
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, backref
from datetime import datetime
import enum

Base = declarative_base()

# ===================================================
# ENUMS
# ===================================================

class MessageRole(enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class TokenType(enum.Enum):
    ACCESS = "access"
    REFRESH = "refresh"
    API = "api"
    EMAIL_VERIFICATION = "email_verification"
    PASSWORD_RESET = "password_reset"

class PaymentStatus(enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"

class InvoiceStatus(enum.Enum):
    DRAFT = "draft"
    SENT = "sent"
    PAID = "paid"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"

# ===================================================
# BENUTZER & AUTHENTIFIZIERUNG
# ===================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, nullable=False)
    username = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255))
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String(255))
    password_reset_token = Column(String(255))
    password_reset_expires = Column(TIMESTAMP)
    last_login = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="user")
    projects = relationship("Project", back_populates="owner")
    api_keys = relationship("ApiKey", back_populates="user")
    tokens = relationship("Token", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    invoices = relationship("Invoice", back_populates="user")
    balance = relationship("UserBalance", back_populates="user", uselist=False)
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}')>"

class Role(Base):
    __tablename__ = "roles"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    user_roles = relationship("UserRole", back_populates="role")
    role_permissions = relationship("RolePermission", back_populates="role")
    
    def __repr__(self):
        return f"<Role(id={self.id}, name='{self.name}')>"

class UserRole(Base):
    __tablename__ = "user_roles"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="user_roles")
    role = relationship("Role", back_populates="user_roles")

class Permission(Base):
    __tablename__ = "permissions"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False)
    resource = Column(String(50), nullable=False)
    action = Column(String(50), nullable=False)
    description = Column(Text)
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    role_permissions = relationship("RolePermission", back_populates="permission")
    
    def __repr__(self):
        return f"<Permission(id={self.id}, name='{self.name}')>"

class RolePermission(Base):
    __tablename__ = "role_permissions"
    
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True)
    permission_id = Column(Integer, ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True)
    assigned_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    role = relationship("Role", back_populates="role_permissions")
    permission = relationship("Permission", back_populates="role_permissions")

# ===================================================
# PROJEKT & ORDNER-STRUKTUR
# ===================================================

class Project(Base):
    __tablename__ = "projects"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    is_shared = Column(Boolean, default=False)
    color = Column(String(7), default="#3B82F6")
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    owner = relationship("User", back_populates="projects")
    folders = relationship("Folder", back_populates="project")
    chats = relationship("Chat", back_populates="project")
    
    def __repr__(self):
        return f"<Project(id={self.id}, name='{self.name}')>"

class Folder(Base):
    __tablename__ = "folders"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    parent_folder_id = Column(Integer, ForeignKey("folders.id", ondelete="CASCADE"))
    color = Column(String(7), default="#6B7280")
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="folders")
    parent_folder = relationship("Folder", remote_side=[id], backref="subfolders")
    chats = relationship("Chat", back_populates="folder")
    
    def __repr__(self):
        return f"<Folder(id={self.id}, name='{self.name}')>"

# ===================================================
# CHAT & NACHRICHTEN
# ===================================================

class Chat(Base):
    __tablename__ = "chats"
    
    id = Column(Integer, primary_key=True)
    title = Column(String(255), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    folder_id = Column(Integer, ForeignKey("folders.id", ondelete="SET NULL"))
    model_name = Column(String(100))
    system_prompt = Column(Text)
    model_config = Column(JSONB, default={})
    temperature = Column(DECIMAL(3, 2), default=0.7)
    max_tokens = Column(Integer, default=4000)
    is_archived = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    project = relationship("Project", back_populates="chats")
    folder = relationship("Folder", back_populates="chats")
    messages = relationship("Message", back_populates="chat")
    usage_logs = relationship("UsageLog", back_populates="chat")
    
    def __repr__(self):
        return f"<Chat(id={self.id}, title='{self.title}')>"

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True)
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0)
    cost = Column(DECIMAL(10, 6), default=0.00)
    metadata = Column(JSONB, default={})
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    chat = relationship("Chat", back_populates="messages")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name="check_message_role"
        ),
    )
    
    def __repr__(self):
        return f"<Message(id={self.id}, role='{self.role}')>"

# ===================================================
# API-SCHLÜSSEL & TOKENS
# ===================================================

class ApiKey(Base):
    __tablename__ = "api_keys"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    provider = Column(String(50), nullable=False)
    key_hash = Column(String(255), nullable=False)
    key_name = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, default=func.now())
    last_used = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="api_keys")
    
    def __repr__(self):
        return f"<ApiKey(id={self.id}, provider='{self.provider}')>"

class Token(Base):
    __tablename__ = "tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    token_hash = Column(String(255), nullable=False)
    token_type = Column(String(50), nullable=False)
    expires_at = Column(TIMESTAMP, nullable=False)
    is_revoked = Column(Boolean, default=False)
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="tokens")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "token_type IN ('access', 'refresh', 'api', 'email_verification', 'password_reset')",
            name="check_token_type"
        ),
    )
    
    def __repr__(self):
        return f"<Token(id={self.id}, type='{self.token_type}')>"

# ===================================================
# USAGE TRACKING & KOSTEN
# ===================================================

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    chat_id = Column(Integer, ForeignKey("chats.id", ondelete="CASCADE"))
    provider = Column(String(50), nullable=False)
    model_name = Column(String(100), nullable=False)
    input_tokens = Column(Integer, default=0)
    output_tokens = Column(Integer, default=0)
    cost = Column(DECIMAL(10, 6), default=0.00)
    currency = Column(String(3), default="USD")
    created_at = Column(TIMESTAMP, default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    chat = relationship("Chat", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, provider='{self.provider}')>"

# ===================================================
# BEZAHLUNG & ABRECHNUNG
# ===================================================

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    stripe_payment_id = Column(String(255), unique=True)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), default="pending")
    payment_method = Column(String(50))
    created_at = Column(TIMESTAMP, default=func.now())
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="payments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending', 'completed', 'failed', 'refunded')",
            name="check_payment_status"
        ),
    )
    
    def __repr__(self):
        return f"<Payment(id={self.id}, amount={self.amount})>"

class Invoice(Base):
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    invoice_number = Column(String(50), unique=True, nullable=False)
    amount = Column(DECIMAL(10, 2), nullable=False)
    currency = Column(String(3), default="USD")
    status = Column(String(50), default="draft")
    tax_amount = Column(DECIMAL(10, 2), default=0.00)
    total_amount = Column(DECIMAL(10, 2), nullable=False)
    created_at = Column(TIMESTAMP, default=func.now())
    due_date = Column(TIMESTAMP, nullable=False)
    paid_at = Column(TIMESTAMP)
    
    # Relationships
    user = relationship("User", back_populates="invoices")
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            "status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')",
            name="check_invoice_status"
        ),
    )
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}')>"

class UserBalance(Base):
    __tablename__ = "user_balance"
    
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    balance = Column(DECIMAL(10, 2), default=0.00)
    currency = Column(String(3), default="USD")
    updated_at = Column(TIMESTAMP, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="balance")
    
    def __repr__(self):
        return f"<UserBalance(user_id={self.user_id}, balance={self.balance})>"

# ===================================================
# INDIZES (definiert in separaten Migrationen)
# ===================================================

# Index-Definitionen werden in Alembic-Migrationen erstellt
# Hier sind sie als Referenz aufgeführt:

# Users
Index('idx_users_email', User.email)
Index('idx_users_username', User.username)
Index('idx_users_is_active', User.is_active)

# Projects
Index('idx_projects_owner', Project.owner_id)
Index('idx_projects_is_shared', Project.is_shared)

# Folders
Index('idx_folders_project', Folder.project_id)
Index('idx_folders_parent', Folder.parent_folder_id)

# Chats
Index('idx_chats_project', Chat.project_id)
Index('idx_chats_folder', Chat.folder_id)
Index('idx_chats_model', Chat.model_name)
Index('idx_chats_archived', Chat.is_archived)

# Messages
Index('idx_messages_chat', Message.chat_id)
Index('idx_messages_role', Message.role)
Index('idx_messages_created_at', Message.created_at)

# API Keys
Index('idx_api_keys_user', ApiKey.user_id)
Index('idx_api_keys_provider', ApiKey.provider)
Index('idx_api_keys_is_active', ApiKey.is_active)

# Tokens
Index('idx_tokens_user', Token.user_id)
Index('idx_tokens_type', Token.token_type)
Index('idx_tokens_expires_at', Token.expires_at)
Index('idx_tokens_is_revoked', Token.is_revoked)

# Usage Logs
Index('idx_usage_logs_user', UsageLog.user_id)
Index('idx_usage_logs_chat', UsageLog.chat_id)
Index('idx_usage_logs_provider', UsageLog.provider)
Index('idx_usage_logs_created_at', UsageLog.created_at)

# Payments
Index('idx_payments_user', Payment.user_id)
Index('idx_payments_status', Payment.status)
Index('idx_payments_created_at', Payment.created_at)

# Invoices
Index('idx_invoices_user', Invoice.user_id)
Index('idx_invoices_status', Invoice.status)
Index('idx_invoices_due_date', Invoice.due_date) 