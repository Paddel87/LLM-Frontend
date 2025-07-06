from fastapi import FastAPI
from logging_config import setup_logging, get_core_logger

# Logging konfigurieren
setup_logging("backend-core")
logger = get_core_logger()

app = FastAPI(title="Backend Core Service", version="0.1.0")

@app.on_event("startup")
async def startup_event():
    logger.info("Backend Core Service starting up")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Backend Core Service shutting down")

@app.get("/")
def read_root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Backend Core Service"}

@app.get("/health")
def health_check():
    logger.debug("Health check endpoint accessed")
    return {"status": "healthy", "service": "backend-core"}