from fastapi import FastAPI
from logging_config import setup_logging, get_auth_logger

# Logging konfigurieren
setup_logging("auth-service")
logger = get_auth_logger()

app = FastAPI(title="Authentication Service", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Authentication Service starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Authentication Service shutting down")

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Authentication Service"}

@app.get("/health")
def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "service": "auth-service"}