"""
Strukturierte Logging-Konfiguration für LLM-Frontend Services
"""
import os
import sys
import logging
from typing import Dict, Any
from datetime import datetime
from pathlib import Path

import structlog
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter mit erweiterten Feldern"""
    
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        super().add_fields(log_record, record, message_dict)
        
        # Erweiterte Felder hinzufügen
        log_record['timestamp'] = datetime.utcnow().isoformat() + 'Z'
        log_record['service'] = os.environ.get('SERVICE_NAME', 'unknown')
        log_record['environment'] = os.environ.get('ENVIRONMENT', 'development')
        log_record['log_level'] = record.levelname
        log_record['logger_name'] = record.name
        
        # Request-ID falls vorhanden
        if hasattr(record, 'request_id'):
            log_record['request_id'] = record.request_id
        
        # User-ID falls vorhanden
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id


def setup_logging(service_name: str = "unknown", log_level: str = "INFO") -> None:
    """
    Konfiguriert strukturiertes Logging für einen Service
    
    Args:
        service_name: Name des Services
        log_level: Logging-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    # Umgebungsvariablen setzen
    os.environ.setdefault('SERVICE_NAME', service_name)
    os.environ.setdefault('LOG_LEVEL', log_level)
    
    # Log-Level von Environment Variable
    level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_format = os.environ.get('LOG_FORMAT', 'json').lower()
    
    # Root Logger konfigurieren
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level))
    
    # Alle Handler entfernen
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Console Handler erstellen
    console_handler = logging.StreamHandler(sys.stdout)
    
    if log_format == 'json':
        # JSON-Format für Produktion
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(service)s %(environment)s %(log_level)s %(logger_name)s %(message)s'
        )
    else:
        # Standard-Format für Entwicklung
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Datei-Handler falls LOG_FILE gesetzt ist
    log_file = os.environ.get('LOG_FILE')
    if log_file:
        # Verzeichnis erstellen falls nicht vorhanden
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Structlog konfigurieren
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer() if log_format == 'json' else structlog.dev.ConsoleRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Uvicorn Logger konfigurieren
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_logger.setLevel(getattr(logging, level))
    
    # FastAPI Logger konfigurieren
    fastapi_logger = logging.getLogger("fastapi")
    fastapi_logger.setLevel(getattr(logging, level))
    
    # SQLAlchemy Logger konfigurieren (weniger verbose)
    sqlalchemy_logger = logging.getLogger("sqlalchemy.engine")
    sqlalchemy_logger.setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Erstellt einen strukturierten Logger für einen bestimmten Kontext
    
    Args:
        name: Name des Loggers (meist __name__)
        
    Returns:
        Konfigurierter structlog Logger
    """
    return structlog.get_logger(name)


def log_request_middleware(request_id: str, user_id: str = None):
    """
    Middleware-Helper für Request-Logging
    
    Args:
        request_id: Eindeutige Request-ID
        user_id: Optional User-ID
    """
    # Request-Kontext an Logger anhängen
    logger = get_logger(__name__)
    return logger.bind(request_id=request_id, user_id=user_id)


# Beispiel für Service-spezifische Logger
def get_auth_logger() -> structlog.stdlib.BoundLogger:
    """Logger für Authentication-Service"""
    return get_logger("auth_service")


def get_api_logger() -> structlog.stdlib.BoundLogger:
    """Logger für API-Gateway"""
    return get_logger("api_gateway")


def get_core_logger() -> structlog.stdlib.BoundLogger:
    """Logger für Backend-Core"""
    return get_logger("backend_core")


def get_llm_logger() -> structlog.stdlib.BoundLogger:
    """Logger für LLM-Proxy"""
    return get_logger("llm_proxy")


def get_rag_logger() -> structlog.stdlib.BoundLogger:
    """Logger für RAG-Service"""
    return get_logger("rag_service")


def get_payment_logger() -> structlog.stdlib.BoundLogger:
    """Logger für Payment-Service"""
    return get_logger("payment_service") 