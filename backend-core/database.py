"""
Database Connection und Session Management für LLM-Frontend
"""
import os
from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from models.database import Base
import structlog

logger = structlog.get_logger(__name__)

# Database URL aus Umgebungsvariable
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@postgres-db:5432/llm_frontend_db"
)

# Engine erstellen
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=os.getenv("DATABASE_DEBUG", "false").lower() == "true"
)

# Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_database() -> Generator[Session, None, None]:
    """
    Dependency für FastAPI um eine Datenbank-Session zu bekommen
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error("Database session error", error=str(e))
        db.rollback()
        raise
    finally:
        db.close()

def init_database():
    """
    Initialisiert die Datenbank (für Tests oder lokale Entwicklung)
    """
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error("Database initialization failed", error=str(e))
        raise

def test_database_connection():
    """
    Testet die Datenbankverbindung
    """
    try:
        with engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("Database connection test successful")
            return True
    except Exception as e:
        logger.error("Database connection test failed", error=str(e))
        return False 