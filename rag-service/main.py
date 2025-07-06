from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime
import uuid
import asyncio
import structlog
from pathlib import Path
import tempfile
import os
from io import BytesIO
import mimetypes
import httpx
import json

# Vector Database und ML
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from qdrant_client.http import models
import numpy as np

# PDF Processing
import PyPDF2

# Lokale Imports
from logging_config import setup_logging, get_rag_logger

# Logging konfigurieren
setup_logging("rag-service")
logger = get_rag_logger()

app = FastAPI(
    title="RAG Service",
    version="0.13.0",
    description="Retrieval-Augmented Generation Service für LLM-Frontend (API-basiert)"
)

# Security
security = HTTPBearer()

# ===================================================
# KONFIGURATION
# ===================================================

# Qdrant Configuration
QDRANT_HOST = os.getenv("QDRANT_HOST", "qdrant")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)

# Embedding API Configuration
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "openai")  # openai, runpod, custom
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")
EMBEDDING_API_KEY = os.getenv("OPENAI_API_KEY", None)  # Primary API key
EMBEDDING_API_BASE = os.getenv("EMBEDDING_API_BASE", "https://api.openai.com/v1")

# RunPod Configuration (alternative)
RUNPOD_EMBEDDING_ENDPOINT = os.getenv("RUNPOD_EMBEDDING_ENDPOINT", None)
RUNPOD_API_KEY = os.getenv("RUNPOD_API_KEY", None)

# LLM Proxy Configuration
LLM_PROXY_URL = os.getenv("LLM_PROXY_URL", "http://llm-proxy:8000")

# Embedding Dimensions by Model
EMBEDDING_DIMENSIONS = {
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    "all-MiniLM-L6-v2": 384,  # Fallback für lokale Tests
}

EMBEDDING_DIMENSION = EMBEDDING_DIMENSIONS.get(EMBEDDING_MODEL, 1536)

# Text Splitting Configuration
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "1000"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "200"))

# Global Variables
qdrant_client = None
http_client = None

# ===================================================
# PYDANTIC MODELS
# ===================================================

class EmbeddingRequest(BaseModel):
    text: str
    model: str = EMBEDDING_MODEL
    provider: str = EMBEDDING_PROVIDER

class EmbeddingResponse(BaseModel):
    embedding: List[float]
    model: str
    usage: Dict[str, Any]
    cost: float

class DocumentUploadRequest(BaseModel):
    project_id: int
    title: str
    description: Optional[str] = None
    tags: Optional[List[str]] = []

class DocumentChunk(BaseModel):
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = None

class DocumentResponse(BaseModel):
    id: str
    title: str
    description: Optional[str]
    project_id: int
    chunk_count: int
    created_at: datetime
    tags: List[str]
    status: str
    embedding_model: str
    embedding_cost: float

class SearchRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    limit: int = Field(default=10, ge=1, le=100)
    score_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class SearchResult(BaseModel):
    id: str
    content: str
    score: float
    metadata: Dict[str, Any]
    document_title: str

class SearchResponse(BaseModel):
    results: List[SearchResult]
    total: int
    query: str
    processing_time: float
    embedding_cost: float

class RAGRequest(BaseModel):
    query: str
    project_id: Optional[int] = None
    max_context_length: int = Field(default=4000, ge=1000, le=8000)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)

class RAGResponse(BaseModel):
    query: str
    context: str
    context_sources: List[Dict[str, Any]]
    processing_time: float
    embedding_cost: float

# ===================================================
# STARTUP & SHUTDOWN
# ===================================================

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    global qdrant_client, http_client
    
    logger.info("Starting RAG Service initialization...")
    
    try:
        # Initialize HTTP Client
        http_client = httpx.AsyncClient(timeout=30.0)
        logger.info("HTTP client initialized")
        
        # Initialize Qdrant Client with retry logic
        max_retries = 10
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Connecting to Qdrant (attempt {attempt + 1}/{max_retries})", 
                           host=QDRANT_HOST, port=QDRANT_PORT)
                
                qdrant_client = QdrantClient(
                    host=QDRANT_HOST,
                    port=QDRANT_PORT,
                    api_key=QDRANT_API_KEY
                )
                
                # Test connection
                collections = qdrant_client.get_collections()
                logger.info("Qdrant connection successful", collections_count=len(collections.collections))
                break
                
            except Exception as e:
                logger.warning(f"Qdrant connection attempt {attempt + 1} failed: {str(e)}")
                if attempt < max_retries - 1:
                    logger.info(f"Retrying in {retry_delay} seconds...")
                    await asyncio.sleep(retry_delay)
                else:
                    logger.error("Failed to connect to Qdrant after all retries")
                    raise
        
        # Log embedding configuration
        logger.info("Embedding configuration", 
                   provider=EMBEDDING_PROVIDER,
                   model=EMBEDDING_MODEL,
                   dimension=EMBEDDING_DIMENSION,
                   api_base=EMBEDDING_API_BASE)
        
        logger.info("Text splitter configuration", chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        
        # Test embedding API only if we have a valid API key
        if EMBEDDING_API_KEY and EMBEDDING_API_KEY != "":
            await test_embedding_api()
        else:
            logger.warning("No embedding API key provided - API calls will fail")
        
        # Ensure default collection exists
        await ensure_collection_exists("documents")
        
        logger.info("RAG Service initialized successfully")
        
    except Exception as e:
        logger.error("Failed to initialize RAG Service", error=str(e))
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down RAG Service...")
    
    if qdrant_client:
        qdrant_client.close()
    
    if http_client:
        await http_client.aclose()
    
    logger.info("RAG Service shutdown complete")

# ===================================================
# EMBEDDING API FUNCTIONS
# ===================================================

async def test_embedding_api():
    """Test the embedding API connection"""
    try:
        logger.info("Testing embedding API connection...")
        
        test_response = await generate_embedding("Hello world test")
        
        if test_response and len(test_response.embedding) == EMBEDDING_DIMENSION:
            logger.info("Embedding API test successful", 
                       dimension=len(test_response.embedding),
                       model=test_response.model,
                       cost=test_response.cost)
        else:
            raise Exception("Embedding API test failed - invalid response")
            
    except Exception as e:
        logger.error("Embedding API test failed", error=str(e))
        raise

async def generate_embedding(text: str) -> EmbeddingResponse:
    """Generate embedding using external API"""
    try:
        if EMBEDDING_PROVIDER == "openai":
            return await generate_openai_embedding(text)
        elif EMBEDDING_PROVIDER == "runpod":
            return await generate_runpod_embedding(text)
        else:
            raise ValueError(f"Unsupported embedding provider: {EMBEDDING_PROVIDER}")
            
    except Exception as e:
        logger.error("Error generating embedding", error=str(e), provider=EMBEDDING_PROVIDER)
        raise HTTPException(status_code=500, detail=f"Failed to generate embedding: {str(e)}")

async def generate_openai_embedding(text: str) -> EmbeddingResponse:
    """Generate embedding using OpenAI API"""
    try:
        headers = {
            "Authorization": f"Bearer {EMBEDDING_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": text,
            "model": EMBEDDING_MODEL,
            "encoding_format": "float"
        }
        
        url = f"{EMBEDDING_API_BASE}/embeddings"
        
        response = await http_client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        
        data = response.json()
        
        # Extract embedding
        embedding = data["data"][0]["embedding"]
        
        # Calculate cost (rough estimate)
        tokens = data["usage"]["total_tokens"]
        cost = calculate_embedding_cost(tokens, EMBEDDING_MODEL)
        
        return EmbeddingResponse(
            embedding=embedding,
            model=EMBEDDING_MODEL,
            usage=data["usage"],
            cost=cost
        )
        
    except Exception as e:
        logger.error("OpenAI embedding generation failed", error=str(e))
        raise

async def generate_runpod_embedding(text: str) -> EmbeddingResponse:
    """Generate embedding using RunPod API"""
    try:
        if not RUNPOD_EMBEDDING_ENDPOINT or not RUNPOD_API_KEY:
            raise ValueError("RunPod embedding configuration missing")
            
        headers = {
            "Authorization": f"Bearer {RUNPOD_API_KEY}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "input": {
                "text": text,
                "model": EMBEDDING_MODEL
            }
        }
        
        response = await http_client.post(
            RUNPOD_EMBEDDING_ENDPOINT,
            json=payload,
            headers=headers
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract embedding (adapt based on RunPod response format)
        if "output" in data and "embedding" in data["output"]:
            embedding = data["output"]["embedding"]
        else:
            raise ValueError("Invalid RunPod response format")
        
        # Estimate cost and usage
        estimated_tokens = len(text.split())
        cost = calculate_embedding_cost(estimated_tokens, EMBEDDING_MODEL, "runpod")
        
        return EmbeddingResponse(
            embedding=embedding,
            model=EMBEDDING_MODEL,
            usage={"total_tokens": estimated_tokens},
            cost=cost
        )
        
    except Exception as e:
        logger.error("RunPod embedding generation failed", error=str(e))
        raise

def calculate_embedding_cost(tokens: int, model: str, provider: str = "openai") -> float:
    """Calculate embedding cost based on tokens and model"""
    # Cost per 1K tokens (in USD)
    cost_per_1k = {
        "openai": {
            "text-embedding-3-small": 0.00002,
            "text-embedding-3-large": 0.00013,
            "text-embedding-ada-002": 0.0001
        },
        "runpod": {
            "default": 0.00001  # Estimated cheaper rate
        }
    }
    
    rate = cost_per_1k.get(provider, {}).get(model, 0.00002)
    return (tokens / 1000) * rate

# ===================================================
# UTILITY FUNCTIONS
# ===================================================

async def ensure_collection_exists(collection_name: str):
    """Ensure a Qdrant collection exists"""
    try:
        collections = qdrant_client.get_collections()
        existing_names = [col.name for col in collections.collections]
        
        if collection_name not in existing_names:
            logger.info("Creating new collection", collection=collection_name)
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(
                    size=EMBEDDING_DIMENSION,
                    distance=Distance.COSINE
                )
            )
            logger.info("Collection created successfully", collection=collection_name)
        else:
            logger.info("Collection already exists", collection=collection_name)
            
    except Exception as e:
        logger.error("Error ensuring collection exists", collection=collection_name, error=str(e))
        raise

def extract_text_from_file(file_path: str, mime_type: str) -> str:
    """Extract text from various file types"""
    try:
        if mime_type.startswith('text/'):
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        elif mime_type == 'application/pdf':
            text = ""
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text
        else:
            # Fallback: try to read as text
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
    except Exception as e:
        logger.error("Error extracting text from file", file_path=file_path, error=str(e))
        raise HTTPException(status_code=400, detail=f"Failed to extract text from file: {str(e)}")

def split_text(text: str, chunk_size: int = CHUNK_SIZE, chunk_overlap: int = CHUNK_OVERLAP) -> List[str]:
    """Split text into chunks with overlap"""
    if len(text) <= chunk_size:
        return [text]
    
    chunks = []
    start = 0
    
    # Separators in order of preference
    separators = ['\n\n', '\n', '. ', ' ', '']
    
    while start < len(text):
        end = start + chunk_size
        
        if end >= len(text):
            chunks.append(text[start:])
            break
        
        # Try to find a good split point
        chunk_end = end
        for separator in separators:
            if separator == '':
                # Last resort: split at chunk_size
                chunk_end = end
                break
            
            # Look for separator within the last 20% of chunk
            search_start = end - int(chunk_size * 0.2)
            sep_pos = text.rfind(separator, search_start, end)
            
            if sep_pos != -1:
                chunk_end = sep_pos + len(separator)
                break
        
        chunks.append(text[start:chunk_end].strip())
        start = max(start + 1, chunk_end - chunk_overlap)
    
    return [chunk for chunk in chunks if chunk.strip()]

def chunk_document(text: str, metadata: Dict[str, Any]) -> List[DocumentChunk]:
    """Split document into chunks"""
    try:
        # Split text into chunks
        text_chunks = split_text(text)
        
        # Convert to DocumentChunk objects
        document_chunks = []
        for i, chunk_text in enumerate(text_chunks):
            chunk_id = str(uuid.uuid4())
            chunk_metadata = {
                **metadata,
                "chunk_index": i,
                "chunk_id": chunk_id
            }
            
            document_chunks.append(DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                metadata=chunk_metadata
            ))
        
        return document_chunks
        
    except Exception as e:
        logger.error("Error chunking document", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to chunk document: {str(e)}")

async def store_chunks_in_qdrant(chunks: List[DocumentChunk], collection_name: str = "documents") -> float:
    """Store document chunks in Qdrant and return total embedding cost"""
    try:
        points = []
        total_cost = 0.0
        
        for chunk in chunks:
            # Generate embedding for chunk using API
            embedding_response = await generate_embedding(chunk.content)
            total_cost += embedding_response.cost
            
            # Create point for Qdrant
            point = PointStruct(
                id=chunk.id,
                vector=embedding_response.embedding,
                payload={
                    "content": chunk.content,
                    "metadata": chunk.metadata
                }
            )
            points.append(point)
        
        # Store in Qdrant
        qdrant_client.upsert(
            collection_name=collection_name,
            points=points
        )
        
        logger.info("Chunks stored successfully", 
                   count=len(chunks), 
                   collection=collection_name,
                   total_cost=total_cost)
        
        return total_cost
        
    except Exception as e:
        logger.error("Error storing chunks in Qdrant", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to store chunks: {str(e)}")

# ===================================================
# AUTHENTICATION
# ===================================================

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Simplified auth for now - in production this would verify JWT"""
    # TODO: Implement proper JWT verification
    return {"user_id": "demo", "username": "demo"}

# ===================================================
# API ENDPOINTS
# ===================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Check Qdrant connection
        collections = qdrant_client.get_collections()
        
        return {
            "status": "healthy",
            "service": "rag-service",
            "timestamp": datetime.utcnow().isoformat(),
            "qdrant_collections": len(collections.collections),
            "embedding_model": EMBEDDING_MODEL
        }
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return {
            "status": "unhealthy",
            "service": "rag-service",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.post("/api/v1/documents/upload", response_model=DocumentResponse)
async def upload_document(
    file: UploadFile = File(...),
    project_id: int = Form(...),
    title: str = Form(...),
    description: Optional[str] = Form(None),
    tags: str = Form(""),
    current_user: Dict = Depends(get_current_user)
):
    """Upload and process a document"""
    start_time = datetime.utcnow()
    document_id = str(uuid.uuid4())
    
    logger.info("Document upload started", document_id=document_id, filename=file.filename)
    
    try:
        # Parse tags
        tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()] if tags else []
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No file provided")
        
        # Get file type
        mime_type, _ = mimetypes.guess_type(file.filename)
        if not mime_type:
            mime_type = "text/plain"
        
        # Save file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Extract text
            text_content = extract_text_from_file(tmp_file_path, mime_type)
            
            # Prepare metadata
            metadata = {
                "document_id": document_id,
                "title": title,
                "description": description,
                "project_id": project_id,
                "filename": file.filename,
                "mime_type": mime_type,
                "tags": tag_list,
                "uploaded_by": current_user["user_id"],
                "uploaded_at": start_time.isoformat(),
                "file_size": len(content)
            }
            
            # Chunk document
            chunks = chunk_document(text_content, metadata)
            
            # Store in Qdrant
            embedding_cost = await store_chunks_in_qdrant(chunks)
            
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            logger.info("Document processed successfully", 
                       document_id=document_id,
                       chunks=len(chunks),
                       processing_time=processing_time)
            
            return DocumentResponse(
                id=document_id,
                title=title,
                description=description,
                project_id=project_id,
                chunk_count=len(chunks),
                created_at=start_time,
                tags=tag_list,
                status="processed",
                embedding_model=EMBEDDING_MODEL,
                embedding_cost=embedding_cost
            )
            
        finally:
            # Clean up temporary file
            os.unlink(tmp_file_path)
            
    except Exception as e:
        logger.error("Document processing failed", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Document processing failed: {str(e)}")

@app.post("/api/v1/search", response_model=SearchResponse)
async def search_documents(
    request: SearchRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Search documents using semantic similarity"""
    start_time = datetime.utcnow()
    
    logger.info("Search started", query=request.query, project_id=request.project_id)
    
    try:
        # Generate query embedding
        query_embedding = await generate_embedding(request.query)
        
        # Prepare search filter
        search_filter = None
        if request.project_id:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.project_id",
                        match=models.MatchValue(value=request.project_id)
                    )
                ]
            )
        
        # Search in Qdrant
        search_results = qdrant_client.search(
            collection_name="documents",
            query_vector=query_embedding.embedding,
            query_filter=search_filter,
            limit=request.limit,
            score_threshold=request.score_threshold
        )
        
        # Format results
        results = []
        for result in search_results:
            results.append(SearchResult(
                id=result.id,
                content=result.payload["content"],
                score=result.score,
                metadata=result.payload["metadata"],
                document_title=result.payload["metadata"].get("title", "Unknown")
            ))
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info("Search completed", 
                   results_count=len(results),
                   processing_time=processing_time,
                   embedding_cost=query_embedding.cost)
        
        return SearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            processing_time=processing_time,
            embedding_cost=query_embedding.cost
        )
        
    except Exception as e:
        logger.error("Search failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@app.post("/api/v1/rag", response_model=RAGResponse)
async def generate_rag_context(
    request: RAGRequest,
    current_user: Dict = Depends(get_current_user)
):
    """Generate RAG context for a query"""
    start_time = datetime.utcnow()
    
    logger.info("RAG context generation started", query=request.query)
    
    try:
        # Search for relevant documents
        search_request = SearchRequest(
            query=request.query,
            project_id=request.project_id,
            limit=20,  # Get more results for context
            score_threshold=request.similarity_threshold
        )
        
        search_response = await search_documents(search_request, current_user)
        
        # Build context from search results
        context_parts = []
        context_sources = []
        current_length = 0
        
        for result in search_response.results:
            # Check if adding this result would exceed max context length
            if current_length + len(result.content) > request.max_context_length:
                break
            
            context_parts.append(result.content)
            context_sources.append({
                "id": result.id,
                "title": result.document_title,
                "score": result.score,
                "chunk_preview": result.content[:100] + "..." if len(result.content) > 100 else result.content
            })
            current_length += len(result.content)
        
        # Combine context
        context = "\n\n".join(context_parts)
        
        processing_time = (datetime.utcnow() - start_time).total_seconds()
        
        logger.info("RAG context generated", 
                   context_length=len(context),
                   sources_count=len(context_sources),
                   processing_time=processing_time,
                   embedding_cost=search_response.embedding_cost)
        
        return RAGResponse(
            query=request.query,
            context=context,
            context_sources=context_sources,
            processing_time=processing_time,
            embedding_cost=search_response.embedding_cost
        )
        
    except Exception as e:
        logger.error("RAG context generation failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"RAG context generation failed: {str(e)}")

@app.get("/api/v1/documents")
async def list_documents(
    project_id: Optional[int] = None,
    limit: int = 50,
    current_user: Dict = Depends(get_current_user)
):
    """List documents with metadata"""
    try:
        # Search with empty query to get all documents
        search_filter = None
        if project_id:
            search_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.project_id",
                        match=models.MatchValue(value=project_id)
                    )
                ]
            )
        
        # Get all points with metadata
        points = qdrant_client.scroll(
            collection_name="documents",
            scroll_filter=search_filter,
            limit=limit,
            with_payload=True,
            with_vectors=False
        )
        
        # Group by document_id
        documents = {}
        for point in points[0]:
            doc_id = point.payload["metadata"]["document_id"]
            if doc_id not in documents:
                documents[doc_id] = {
                    "id": doc_id,
                    "title": point.payload["metadata"]["title"],
                    "description": point.payload["metadata"].get("description"),
                    "project_id": point.payload["metadata"]["project_id"],
                    "tags": point.payload["metadata"].get("tags", []),
                    "created_at": point.payload["metadata"]["uploaded_at"],
                    "chunk_count": 0,
                    "status": "processed"
                }
            documents[doc_id]["chunk_count"] += 1
        
        return {
            "documents": list(documents.values()),
            "total": len(documents)
        }
        
    except Exception as e:
        logger.error("Failed to list documents", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")

@app.delete("/api/v1/documents/{document_id}")
async def delete_document(
    document_id: str,
    current_user: Dict = Depends(get_current_user)
):
    """Delete a document and all its chunks"""
    try:
        # Find all chunks for this document
        points = qdrant_client.scroll(
            collection_name="documents",
            scroll_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="metadata.document_id",
                        match=models.MatchValue(value=document_id)
                    )
                ]
            ),
            with_payload=False,
            with_vectors=False
        )
        
        # Delete all chunks
        point_ids = [point.id for point in points[0]]
        
        if point_ids:
            qdrant_client.delete(
                collection_name="documents",
                points_selector=models.PointIdsList(points=point_ids)
            )
        
        logger.info("Document deleted", document_id=document_id, chunks_deleted=len(point_ids))
        
        return {
            "message": "Document deleted successfully",
            "document_id": document_id,
            "chunks_deleted": len(point_ids)
        }
        
    except Exception as e:
        logger.error("Failed to delete document", document_id=document_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@app.get("/api/v1/collections")
async def list_collections():
    """List all Qdrant collections"""
    try:
        collections = qdrant_client.get_collections()
        return {
            "collections": [
                {
                    "name": col.name,
                    "status": col.status,
                    "points_count": qdrant_client.count(col.name).count if col.status == "green" else 0
                }
                for col in collections.collections
            ]
        }
    except Exception as e:
        logger.error("Failed to list collections", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")

# ===================================================
# ROOT ENDPOINT
# ===================================================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "RAG Service - Retrieval-Augmented Generation",
        "version": "0.13.0",
        "service": "rag-service",
        "status": "running",
        "features": [
            "Document Upload & Processing",
            "Vector Search",
            "RAG Context Generation",
            "Multiple File Types Support",
            "Qdrant Vector Database"
        ]
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)