from fastapi import FastAPI, Depends, HTTPException, status, Query, File, UploadFile, Form
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime
import structlog
from io import BytesIO, StringIO
import zipfile
import json
import csv

from logging_config import setup_logging, get_core_logger
from database import get_database, init_database
from models.database import User, Project, Folder, Chat, Message, MessageRole
from utils.auth import get_current_user, verify_jwt_token

# Logging konfigurieren
setup_logging("backend-core")
logger = get_core_logger()

app = FastAPI(
    title="Backend Core Service", 
    version="0.6.0",
    description="Core Backend Service für LLM-Frontend - Project & Chat Management"
)

# Security
security = HTTPBearer()

# ===================================================
# AUTHENTICATION DEPENDENCY
# ===================================================

async def get_current_user_dependency(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database)
) -> User:
    """
    FastAPI Dependency für die Benutzerauthentifizierung
    """
    token = credentials.credentials
    payload = verify_jwt_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    user = get_current_user(db, payload.get("user_id"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

# ===================================================
# PYDANTIC MODELS
# ===================================================

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(default="#3B82F6", regex="^#[0-9A-Fa-f]{6}$")
    is_shared: bool = False

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    is_shared: Optional[bool] = None

class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class FolderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    color: str = Field(default="#6B7280", regex="^#[0-9A-Fa-f]{6}$")
    parent_folder_id: Optional[int] = None

class FolderCreate(FolderBase):
    project_id: int

class FolderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    parent_folder_id: Optional[int] = None

class FolderResponse(FolderBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class ChatBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=4000, ge=1, le=32000)
    model_config: dict = Field(default_factory=dict)

class ChatCreate(ChatBase):
    project_id: int
    folder_id: Optional[int] = None

class ChatUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    model_name: Optional[str] = None
    system_prompt: Optional[str] = None
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    max_tokens: Optional[int] = Field(None, ge=1, le=32000)
    model_config: Optional[dict] = None
    folder_id: Optional[int] = None
    is_archived: Optional[bool] = None

class ChatResponse(ChatBase):
    id: int
    project_id: int
    folder_id: Optional[int]
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class MessageBase(BaseModel):
    role: MessageRole
    content: str = Field(..., min_length=1)
    metadata: dict = Field(default_factory=dict)

class MessageCreate(MessageBase):
    chat_id: int

class MessageResponse(MessageBase):
    id: int
    chat_id: int
    token_count: int
    cost: float
    created_at: datetime
    
    class Config:
        from_attributes = True

# ===================================================
# STARTUP/SHUTDOWN EVENTS
# ===================================================

@app.on_event("startup")
async def startup_event():
    logger.info("Backend Core Service starting up")
    try:
        init_database()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend Core Service shutting down")

# ===================================================
# HEALTH CHECK
# ===================================================

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Backend Core Service v0.6.0 - Project & Chat Management"}

@app.get("/health")
def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "service": "backend-core", "version": "0.6.0"}

# ===================================================
# PROJECT CRUD OPERATIONS
# ===================================================

@app.post("/api/v1/projects", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project: ProjectCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Erstelle ein neues Projekt
    """
    logger.info("Creating new project", user_id=current_user.id, project_name=project.name)
    
    db_project = Project(
        name=project.name,
        description=project.description,
        color=project.color,
        is_shared=project.is_shared,
        owner_id=current_user.id
    )
    
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    
    logger.info("Project created successfully", project_id=db_project.id)
    return db_project

@app.get("/api/v1/projects", response_model=List[ProjectResponse])
def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    search: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole alle Projekte des aktuellen Benutzers
    """
    logger.debug("Fetching projects", user_id=current_user.id, skip=skip, limit=limit)
    
    query = db.query(Project).filter(Project.owner_id == current_user.id)
    
    if search:
        query = query.filter(
            Project.name.ilike(f"%{search}%") | 
            Project.description.ilike(f"%{search}%")
        )
    
    projects = query.offset(skip).limit(limit).all()
    
    logger.debug("Projects fetched", count=len(projects))
    return projects

@app.get("/api/v1/projects/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole ein spezifisches Projekt
    """
    logger.debug("Fetching project", project_id=project_id, user_id=current_user.id)
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    return project

@app.put("/api/v1/projects/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Aktualisiere ein Projekt
    """
    logger.info("Updating project", project_id=project_id, user_id=current_user.id)
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found for update", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Update nur gesetzte Felder
    update_data = project_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)
    
    db.commit()
    db.refresh(project)
    
    logger.info("Project updated successfully", project_id=project_id)
    return project

@app.delete("/api/v1/projects/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Lösche ein Projekt
    """
    logger.info("Deleting project", project_id=project_id, user_id=current_user.id)
    
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found for deletion", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    db.delete(project)
    db.commit()
    
    logger.info("Project deleted successfully", project_id=project_id)

# ===================================================
# FOLDER CRUD OPERATIONS
# ===================================================

@app.post("/api/v1/folders", response_model=FolderResponse, status_code=status.HTTP_201_CREATED)
def create_folder(
    folder: FolderCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Erstelle einen neuen Ordner
    """
    logger.info("Creating new folder", user_id=current_user.id, folder_name=folder.name)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == folder.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found for folder creation", project_id=folder.project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify parent folder if specified
    if folder.parent_folder_id:
        parent_folder = db.query(Folder).filter(
            Folder.id == folder.parent_folder_id,
            Folder.project_id == folder.project_id
        ).first()
        
        if not parent_folder:
            logger.warning("Parent folder not found", parent_folder_id=folder.parent_folder_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
    
    db_folder = Folder(
        name=folder.name,
        description=folder.description,
        color=folder.color,
        project_id=folder.project_id,
        parent_folder_id=folder.parent_folder_id
    )
    
    db.add(db_folder)
    db.commit()
    db.refresh(db_folder)
    
    logger.info("Folder created successfully", folder_id=db_folder.id)
    return db_folder

@app.get("/api/v1/projects/{project_id}/folders", response_model=List[FolderResponse])
def get_project_folders(
    project_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole alle Ordner eines Projekts
    """
    logger.debug("Fetching project folders", project_id=project_id, user_id=current_user.id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    folders = db.query(Folder).filter(Folder.project_id == project_id).all()
    
    logger.debug("Folders fetched", count=len(folders))
    return folders

@app.get("/api/v1/folders/{folder_id}", response_model=FolderResponse)
def get_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole einen spezifischen Ordner
    """
    logger.debug("Fetching folder", folder_id=folder_id, user_id=current_user.id)
    
    folder = db.query(Folder).join(Project).filter(
        Folder.id == folder_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not folder:
        logger.warning("Folder not found", folder_id=folder_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    return folder

@app.put("/api/v1/folders/{folder_id}", response_model=FolderResponse)
def update_folder(
    folder_id: int,
    folder_update: FolderUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Aktualisiere einen Ordner
    """
    logger.info("Updating folder", folder_id=folder_id, user_id=current_user.id)
    
    folder = db.query(Folder).join(Project).filter(
        Folder.id == folder_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not folder:
        logger.warning("Folder not found for update", folder_id=folder_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    # Verify parent folder if specified
    if folder_update.parent_folder_id:
        parent_folder = db.query(Folder).filter(
            Folder.id == folder_update.parent_folder_id,
            Folder.project_id == folder.project_id
        ).first()
        
        if not parent_folder:
            logger.warning("Parent folder not found", parent_folder_id=folder_update.parent_folder_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent folder not found"
            )
    
    # Update nur gesetzte Felder
    update_data = folder_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)
    
    db.commit()
    db.refresh(folder)
    
    logger.info("Folder updated successfully", folder_id=folder_id)
    return folder

@app.delete("/api/v1/folders/{folder_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_folder(
    folder_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Lösche einen Ordner
    """
    logger.info("Deleting folder", folder_id=folder_id, user_id=current_user.id)
    
    folder = db.query(Folder).join(Project).filter(
        Folder.id == folder_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not folder:
        logger.warning("Folder not found for deletion", folder_id=folder_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Folder not found"
        )
    
    db.delete(folder)
    db.commit()
    
    logger.info("Folder deleted successfully", folder_id=folder_id)

# ===================================================
# CHAT CRUD OPERATIONS
# ===================================================

@app.post("/api/v1/chats", response_model=ChatResponse, status_code=status.HTTP_201_CREATED)
def create_chat(
    chat: ChatCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Erstelle einen neuen Chat
    """
    logger.info("Creating new chat", user_id=current_user.id, chat_title=chat.title)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == chat.project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found for chat creation", project_id=chat.project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    # Verify folder if specified
    if chat.folder_id:
        folder = db.query(Folder).filter(
            Folder.id == chat.folder_id,
            Folder.project_id == chat.project_id
        ).first()
        
        if not folder:
            logger.warning("Folder not found", folder_id=chat.folder_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    db_chat = Chat(
        title=chat.title,
        model_name=chat.model_name,
        system_prompt=chat.system_prompt,
        temperature=chat.temperature,
        max_tokens=chat.max_tokens,
        model_config=chat.model_config,
        project_id=chat.project_id,
        folder_id=chat.folder_id
    )
    
    db.add(db_chat)
    db.commit()
    db.refresh(db_chat)
    
    logger.info("Chat created successfully", chat_id=db_chat.id)
    return db_chat

@app.get("/api/v1/projects/{project_id}/chats", response_model=List[ChatResponse])
def get_project_chats(
    project_id: int,
    folder_id: Optional[int] = Query(None),
    include_archived: bool = Query(False),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole alle Chats eines Projekts
    """
    logger.debug("Fetching project chats", project_id=project_id, user_id=current_user.id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        logger.warning("Project not found", project_id=project_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Project not found"
        )
    
    query = db.query(Chat).filter(Chat.project_id == project_id)
    
    if folder_id:
        query = query.filter(Chat.folder_id == folder_id)
    
    if not include_archived:
        query = query.filter(Chat.is_archived == False)
    
    chats = query.offset(skip).limit(limit).all()
    
    logger.debug("Chats fetched", count=len(chats))
    return chats

@app.get("/api/v1/chats/{chat_id}", response_model=ChatResponse)
def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole einen spezifischen Chat
    """
    logger.debug("Fetching chat", chat_id=chat_id, user_id=current_user.id)
    
    chat = db.query(Chat).join(Project).filter(
        Chat.id == chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        logger.warning("Chat not found", chat_id=chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    return chat

@app.put("/api/v1/chats/{chat_id}", response_model=ChatResponse)
def update_chat(
    chat_id: int,
    chat_update: ChatUpdate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Aktualisiere einen Chat
    """
    logger.info("Updating chat", chat_id=chat_id, user_id=current_user.id)
    
    chat = db.query(Chat).join(Project).filter(
        Chat.id == chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        logger.warning("Chat not found for update", chat_id=chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    # Verify folder if specified
    if chat_update.folder_id:
        folder = db.query(Folder).filter(
            Folder.id == chat_update.folder_id,
            Folder.project_id == chat.project_id
        ).first()
        
        if not folder:
            logger.warning("Folder not found", folder_id=chat_update.folder_id)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Folder not found"
            )
    
    # Update nur gesetzte Felder
    update_data = chat_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chat, field, value)
    
    db.commit()
    db.refresh(chat)
    
    logger.info("Chat updated successfully", chat_id=chat_id)
    return chat

@app.delete("/api/v1/chats/{chat_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Lösche einen Chat
    """
    logger.info("Deleting chat", chat_id=chat_id, user_id=current_user.id)
    
    chat = db.query(Chat).join(Project).filter(
        Chat.id == chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        logger.warning("Chat not found for deletion", chat_id=chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    db.delete(chat)
    db.commit()
    
    logger.info("Chat deleted successfully", chat_id=chat_id)

# ===================================================
# MESSAGE CRUD OPERATIONS
# ===================================================

@app.post("/api/v1/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def create_message(
    message: MessageCreate,
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Erstelle eine neue Nachricht
    """
    logger.info("Creating new message", user_id=current_user.id, chat_id=message.chat_id)
    
    # Verify chat ownership
    chat = db.query(Chat).join(Project).filter(
        Chat.id == message.chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        logger.warning("Chat not found for message creation", chat_id=message.chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    db_message = Message(
        chat_id=message.chat_id,
        role=message.role.value,
        content=message.content,
        metadata=message.metadata
    )
    
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    
    logger.info("Message created successfully", message_id=db_message.id)
    return db_message

@app.get("/api/v1/chats/{chat_id}/messages", response_model=List[MessageResponse])
def get_chat_messages(
    chat_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Hole alle Nachrichten eines Chats
    """
    logger.debug("Fetching chat messages", chat_id=chat_id, user_id=current_user.id)
    
    # Verify chat ownership
    chat = db.query(Chat).join(Project).filter(
        Chat.id == chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        logger.warning("Chat not found", chat_id=chat_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )
    
    messages = db.query(Message).filter(
        Message.chat_id == chat_id
    ).order_by(Message.created_at.asc()).offset(skip).limit(limit).all()
    
    logger.debug("Messages fetched", count=len(messages))
    return messages

# ===================================================
# BATCH OPERATIONS
# ===================================================

@app.post("/api/v1/projects/batch/archive")
def batch_archive_projects(
    project_ids: List[int],
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Archiviere mehrere Projekte auf einmal
    """
    logger.info("Batch archiving projects", user_id=current_user.id, project_count=len(project_ids))
    
    updated_count = db.query(Project).filter(
        Project.id.in_(project_ids),
        Project.owner_id == current_user.id
    ).update({"is_archived": True}, synchronize_session=False)
    
    db.commit()
    
    logger.info("Projects archived", count=updated_count)
    return {"message": f"Successfully archived {updated_count} projects"}

@app.post("/api/v1/chats/batch/archive")
def batch_archive_chats(
    chat_ids: List[int],
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Archiviere mehrere Chats auf einmal
    """
    logger.info("Batch archiving chats", user_id=current_user.id, chat_count=len(chat_ids))
    
    # Verify ownership through join
    updated_count = db.query(Chat).join(Project).filter(
        Chat.id.in_(chat_ids),
        Project.owner_id == current_user.id
    ).update({"is_archived": True}, synchronize_session=False)
    
    db.commit()
    
    logger.info("Chats archived", count=updated_count)
    return {"message": f"Successfully archived {updated_count} chats"}

# ===================================================
# SEARCH AND FILTER OPERATIONS
# ===================================================

@app.get("/api/v1/search", response_model=dict)
def search_content(
    query: str = Query(..., min_length=1),
    search_type: str = Query("all", regex="^(all|projects|chats|messages)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Suche nach Inhalten in Projekten, Chats und Nachrichten
    """
    logger.info("Searching content", user_id=current_user.id, query=query, search_type=search_type)
    
    results = {}
    
    if search_type in ["all", "projects"]:
        projects = db.query(Project).filter(
            Project.owner_id == current_user.id,
            Project.name.ilike(f"%{query}%") | Project.description.ilike(f"%{query}%")
        ).limit(10).all()
        results["projects"] = [ProjectResponse.from_orm(p) for p in projects]
    
    if search_type in ["all", "chats"]:
        chats = db.query(Chat).join(Project).filter(
            Project.owner_id == current_user.id,
            Chat.title.ilike(f"%{query}%") | Chat.system_prompt.ilike(f"%{query}%")
        ).limit(10).all()
        results["chats"] = [ChatResponse.from_orm(c) for c in chats]
    
    if search_type in ["all", "messages"]:
        messages = db.query(Message).join(Chat).join(Project).filter(
            Project.owner_id == current_user.id,
            Message.content.ilike(f"%{query}%")
        ).limit(10).all()
        results["messages"] = [MessageResponse.from_orm(m) for m in messages]
    
    logger.info("Search completed", results_count=sum(len(v) for v in results.values()))
    return results

# ===================================================
# IMPORT/EXPORT OPERATIONS
# ===================================================

class ImportExportService:
    """
    Service für Import/Export von Chat-Daten
    """
    
    @staticmethod
    def parse_chatgpt_export(file_content: bytes) -> Dict[str, Any]:
        """
        Parse ChatGPT Export JSON
        """
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            parsed_data = {
                "conversations": [],
                "total_conversations": 0,
                "import_summary": {
                    "messages_count": 0,
                    "conversations_count": 0,
                    "earliest_date": None,
                    "latest_date": None
                }
            }
            
            # ChatGPT Export Format
            for conversation in data:
                if not isinstance(conversation, dict):
                    continue
                
                conversation_data = {
                    "title": conversation.get("title", "Untitled Chat"),
                    "create_time": conversation.get("create_time"),
                    "update_time": conversation.get("update_time"),
                    "messages": []
                }
                
                # Parse messages
                mapping = conversation.get("mapping", {})
                for node_id, node in mapping.items():
                    message = node.get("message")
                    if not message:
                        continue
                    
                    content = message.get("content", {})
                    if content.get("content_type") == "text":
                        parts = content.get("parts", [])
                        if parts:
                            conversation_data["messages"].append({
                                "role": message.get("author", {}).get("role", "unknown"),
                                "content": parts[0] if isinstance(parts[0], str) else str(parts[0]),
                                "create_time": message.get("create_time"),
                                "id": node_id
                            })
                
                if conversation_data["messages"]:
                    parsed_data["conversations"].append(conversation_data)
                    parsed_data["import_summary"]["messages_count"] += len(conversation_data["messages"])
            
            parsed_data["import_summary"]["conversations_count"] = len(parsed_data["conversations"])
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing ChatGPT export: {e}")
    
    @staticmethod
    def parse_typingmind_export(file_content: bytes) -> Dict[str, Any]:
        """
        Parse TypingMind Export JSON
        """
        try:
            data = json.loads(file_content.decode('utf-8'))
            
            parsed_data = {
                "conversations": [],
                "total_conversations": 0,
                "import_summary": {
                    "messages_count": 0,
                    "conversations_count": 0,
                    "earliest_date": None,
                    "latest_date": None
                }
            }
            
            # TypingMind Export Format
            chats = data.get("chats", [])
            for chat in chats:
                if not isinstance(chat, dict):
                    continue
                
                conversation_data = {
                    "title": chat.get("name", "Untitled Chat"),
                    "create_time": chat.get("createdAt"),
                    "update_time": chat.get("updatedAt"),
                    "model": chat.get("model"),
                    "system_prompt": chat.get("systemPrompt"),
                    "messages": []
                }
                
                # Parse messages
                messages = chat.get("messages", [])
                for message in messages:
                    if isinstance(message, dict):
                        conversation_data["messages"].append({
                            "role": message.get("role", "unknown"),
                            "content": message.get("content", ""),
                            "create_time": message.get("createdAt"),
                            "id": message.get("id")
                        })
                
                if conversation_data["messages"]:
                    parsed_data["conversations"].append(conversation_data)
                    parsed_data["import_summary"]["messages_count"] += len(conversation_data["messages"])
            
            parsed_data["import_summary"]["conversations_count"] = len(parsed_data["conversations"])
            
            return parsed_data
            
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")
        except Exception as e:
            raise ValueError(f"Error parsing TypingMind export: {e}")
    
    @staticmethod
    def import_conversations_to_db(
        db: Session,
        parsed_data: Dict[str, Any],
        user_id: int,
        project_id: int,
        folder_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Import parsed conversations to database
        """
        import_results = {
            "imported_chats": 0,
            "imported_messages": 0,
            "errors": []
        }
        
        try:
            for conversation in parsed_data["conversations"]:
                try:
                    # Create chat
                    chat = Chat(
                        title=conversation["title"],
                        project_id=project_id,
                        folder_id=folder_id,
                        model_name=conversation.get("model", "gpt-3.5-turbo"),
                        system_prompt=conversation.get("system_prompt", "")
                    )
                    
                    db.add(chat)
                    db.flush()  # Get ID but don't commit yet
                    
                    # Create messages
                    for message_data in conversation["messages"]:
                        message = Message(
                            chat_id=chat.id,
                            role=message_data["role"],
                            content=message_data["content"],
                            metadata={"imported": True, "original_id": message_data.get("id")}
                        )
                        db.add(message)
                    
                    import_results["imported_chats"] += 1
                    import_results["imported_messages"] += len(conversation["messages"])
                    
                except Exception as e:
                    import_results["errors"].append(f"Error importing chat '{conversation['title']}': {e}")
                    continue
            
            db.commit()
            
        except Exception as e:
            db.rollback()
            raise ValueError(f"Database import failed: {e}")
        
        return import_results

@app.post("/api/v1/import/chatgpt")
async def import_chatgpt(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Import ChatGPT conversation export
    """
    logger.info("Importing ChatGPT export", user_id=current_user.id, project_id=project_id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify folder if specified
    if folder_id:
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.project_id == project_id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse ChatGPT export
        parsed_data = ImportExportService.parse_chatgpt_export(file_content)
        
        # Import to database
        import_results = ImportExportService.import_conversations_to_db(
            db, parsed_data, current_user.id, project_id, folder_id
        )
        
        logger.info("ChatGPT import completed", 
                   imported_chats=import_results["imported_chats"],
                   imported_messages=import_results["imported_messages"])
        
        return {
            "success": True,
            "message": "ChatGPT export imported successfully",
            "summary": {
                "imported_chats": import_results["imported_chats"],
                "imported_messages": import_results["imported_messages"],
                "errors": import_results["errors"]
            }
        }
        
    except ValueError as e:
        logger.error("ChatGPT import validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("ChatGPT import error", error=str(e))
        raise HTTPException(status_code=500, detail="Import failed")

@app.post("/api/v1/import/typingmind")
async def import_typingmind(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    folder_id: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Import TypingMind conversation export
    """
    logger.info("Importing TypingMind export", user_id=current_user.id, project_id=project_id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Verify folder if specified
    if folder_id:
        folder = db.query(Folder).filter(
            Folder.id == folder_id,
            Folder.project_id == project_id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")
    
    try:
        # Read file content
        file_content = await file.read()
        
        # Parse TypingMind export
        parsed_data = ImportExportService.parse_typingmind_export(file_content)
        
        # Import to database
        import_results = ImportExportService.import_conversations_to_db(
            db, parsed_data, current_user.id, project_id, folder_id
        )
        
        logger.info("TypingMind import completed",
                   imported_chats=import_results["imported_chats"],
                   imported_messages=import_results["imported_messages"])
        
        return {
            "success": True,
            "message": "TypingMind export imported successfully",
            "summary": {
                "imported_chats": import_results["imported_chats"],
                "imported_messages": import_results["imported_messages"],
                "errors": import_results["errors"]
            }
        }
        
    except ValueError as e:
        logger.error("TypingMind import validation error", error=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("TypingMind import error", error=str(e))
        raise HTTPException(status_code=500, detail="Import failed")

@app.post("/api/v1/import/bulk")
async def bulk_import_conversations(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    folder_id: Optional[int] = Form(None),
    import_format: str = Form(..., regex="^(chatgpt|typingmind|generic)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Bulk import conversations from various formats
    """
    logger.info("Bulk importing conversations", 
               format=import_format,
               user_id=current_user.id, 
               project_id=project_id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        file_content = await file.read()
        
        if import_format == "chatgpt":
            parsed_data = ImportExportService.parse_chatgpt_export(file_content)
        elif import_format == "typingmind":
            parsed_data = ImportExportService.parse_typingmind_export(file_content)
        else:
            raise ValueError(f"Unsupported import format: {import_format}")
        
        # Import to database
        import_results = ImportExportService.import_conversations_to_db(
            db, parsed_data, current_user.id, project_id, folder_id
        )
        
        logger.info("Bulk import completed",
                   format=import_format,
                   imported_chats=import_results["imported_chats"],
                   imported_messages=import_results["imported_messages"])
        
        return {
            "success": True,
            "message": f"Bulk import ({import_format}) completed successfully",
            "summary": import_results
        }
        
    except Exception as e:
        logger.error("Bulk import error", error=str(e))
        raise HTTPException(status_code=500, detail="Bulk import failed")

@app.get("/api/v1/export/project/{project_id}")
async def export_project(
    project_id: int,
    format: str = Query("json", regex="^(json|markdown|csv)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Export project data in various formats
    """
    logger.info("Exporting project", project_id=project_id, format=format, user_id=current_user.id)
    
    # Verify project ownership
    project = db.query(Project).filter(
        Project.id == project_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Get all chats and messages
    chats = db.query(Chat).filter(Chat.project_id == project_id).all()
    
    export_data = {
        "project": {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat()
        },
        "chats": [],
        "export_info": {
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
            "total_chats": len(chats),
            "total_messages": 0
        }
    }
    
    for chat in chats:
        messages = db.query(Message).filter(Message.chat_id == chat.id).order_by(Message.created_at.asc()).all()
        
        chat_data = {
            "id": chat.id,
            "title": chat.title,
            "model_name": chat.model_name,
            "system_prompt": chat.system_prompt,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat(),
            "messages": [
                {
                    "id": msg.id,
                    "role": msg.role,
                    "content": msg.content,
                    "created_at": msg.created_at.isoformat(),
                    "token_count": msg.token_count,
                    "cost": float(msg.cost) if msg.cost else 0.0
                }
                for msg in messages
            ]
        }
        
        export_data["chats"].append(chat_data)
        export_data["export_info"]["total_messages"] += len(messages)
    
    if format == "json":
        return export_data
    elif format == "markdown":
        markdown_content = f"# {project.name}\n\n"
        markdown_content += f"**Description:** {project.description or 'No description'}\n\n"
        markdown_content += f"**Exported:** {datetime.utcnow().isoformat()}\n\n"
        
        for chat_data in export_data["chats"]:
            markdown_content += f"## {chat_data['title']}\n\n"
            markdown_content += f"**Model:** {chat_data['model_name']}\n\n"
            
            if chat_data['system_prompt']:
                markdown_content += f"**System Prompt:** {chat_data['system_prompt']}\n\n"
            
            for message in chat_data['messages']:
                markdown_content += f"### {message['role'].title()}\n\n"
                markdown_content += f"{message['content']}\n\n"
                markdown_content += f"*{message['created_at']}*\n\n---\n\n"
        
        return PlainTextResponse(markdown_content, media_type="text/markdown")
    
    elif format == "csv":
        # Create CSV data
        csv_data = []
        for chat_data in export_data["chats"]:
            for message in chat_data['messages']:
                csv_data.append({
                    "project_name": project.name,
                    "chat_title": chat_data['title'],
                    "chat_model": chat_data['model_name'],
                    "message_role": message['role'],
                    "message_content": message['content'],
                    "message_date": message['created_at'],
                    "token_count": message['token_count'],
                    "cost": message['cost']
                })
        
        # Convert to CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=csv_data[0].keys() if csv_data else [])
        writer.writeheader()
        writer.writerows(csv_data)
        
        return PlainTextResponse(output.getvalue(), media_type="text/csv")

@app.get("/api/v1/export/chat/{chat_id}")
async def export_chat(
    chat_id: int,
    format: str = Query("json", regex="^(json|markdown|txt)$"),
    current_user: User = Depends(get_current_user_dependency),
    db: Session = Depends(get_database)
):
    """
    Export single chat in various formats
    """
    logger.info("Exporting chat", chat_id=chat_id, format=format, user_id=current_user.id)
    
    # Verify chat ownership
    chat = db.query(Chat).join(Project).filter(
        Chat.id == chat_id,
        Project.owner_id == current_user.id
    ).first()
    
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get messages
    messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at.asc()).all()
    
    export_data = {
        "chat": {
            "id": chat.id,
            "title": chat.title,
            "model_name": chat.model_name,
            "system_prompt": chat.system_prompt,
            "created_at": chat.created_at.isoformat(),
            "updated_at": chat.updated_at.isoformat()
        },
        "messages": [
            {
                "id": msg.id,
                "role": msg.role,
                "content": msg.content,
                "created_at": msg.created_at.isoformat(),
                "token_count": msg.token_count,
                "cost": float(msg.cost) if msg.cost else 0.0
            }
            for msg in messages
        ],
        "export_info": {
            "exported_at": datetime.utcnow().isoformat(),
            "format": format,
            "total_messages": len(messages)
        }
    }
    
    if format == "json":
        return export_data
    elif format == "markdown":
        markdown_content = f"# {chat.title}\n\n"
        markdown_content += f"**Model:** {chat.model_name}\n\n"
        
        if chat.system_prompt:
            markdown_content += f"**System Prompt:** {chat.system_prompt}\n\n"
        
        for message in export_data["messages"]:
            markdown_content += f"## {message['role'].title()}\n\n"
            markdown_content += f"{message['content']}\n\n"
            markdown_content += f"*{message['created_at']}*\n\n---\n\n"
        
        return PlainTextResponse(markdown_content, media_type="text/markdown")
    
    elif format == "txt":
        txt_content = f"{chat.title}\n" + "="*len(chat.title) + "\n\n"
        txt_content += f"Model: {chat.model_name}\n\n"
        
        if chat.system_prompt:
            txt_content += f"System Prompt: {chat.system_prompt}\n\n"
        
        for message in export_data["messages"]:
            txt_content += f"{message['role'].upper()}: {message['content']}\n\n"
        
        return PlainTextResponse(txt_content, media_type="text/plain")

# ===================================================
# ADDITIONAL IMPORTS
# ===================================================

from fastapi.responses import PlainTextResponse