# 🛠️ LLM-Frontend Entwicklungsanleitung v0.13.0

## 📋 Übersicht

Dieses Dokument beschreibt die Einrichtung und Entwicklung des **LLM-Frontend** Projekts. Das System besteht aus mehreren Microservices, die über Docker Compose orchestriert werden.

**🎯 Aktueller Status:** Version 0.13.0 - Milestone 4.1 RAG & Vector Database abgeschlossen

## 🎯 Systemarchitektur

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│     Frontend    │    │   API Gateway   │    │  Backend Core   │
│   (React/Vite)  │◄──►│   (Node.js)     │◄──►│   (FastAPI)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Auth Service  │
                    │   (FastAPI)     │
                    └─────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┬─────────────────────┐
        ▼                     ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Payment Svc    │  │   LLM Proxy     │  │   RAG Service   │  │   Vector DB     │
│  (FastAPI)      │  │   (FastAPI)     │  │   (FastAPI)     │  │   (Qdrant)      │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │                     │
        ▼                     ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │   LLM APIs      │  │  Embedding APIs │  │   Documents     │
│   (Database)    │  │ (OpenAI, etc.)  │  │ (OpenAI, RunPod)│  │   (Storage)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔧 Systemvoraussetzungen

### Minimal Requirements (Optimiert für v0.13.0)
- **Docker**: >= 24.0
- **Docker Compose**: >= 2.20
- **Git**: >= 2.30
- **Node.js**: >= 18.0 (für lokale Entwicklung)
- **Python**: >= 3.11 (für lokale Entwicklung)

### Empfohlene Systemspezifikationen (Reduziert durch API-basierte Architektur)
- **RAM**: 4GB+ (8GB empfohlen) - 50% Reduktion durch keine lokalen ML-Models
- **CPU**: 2+ Kerne (4+ empfohlen)
- **Disk**: 10GB+ freier Speicherplatz - 50% Reduktion durch optimierte Docker Images
- **OS**: Linux, macOS, oder Windows mit WSL2
- **🚫 Keine lokalen GPUs erforderlich** - Vollständig API-basiert

### Software-Versionen
```bash
# Versionen prüfen
docker --version          # >= 24.0.0
docker-compose --version  # >= 2.20.0
node --version            # >= 18.0.0
python3 --version         # >= 3.11.0
git --version             # >= 2.30.0
```

## 🚀 Schnellstart

### 1. Repository klonen
```bash
git clone https://github.com/yourusername/llm-frontend.git
cd llm-frontend
```

### 2. Automatisches Setup
```bash
# Vollständiges Setup mit einem Befehl
./scripts/dev-setup.sh

# Mit Development-Tools
./scripts/dev-setup.sh --with-tools
```

### 3. Services starten
```bash
# Alle Services starten
docker-compose up -d

# Logs verfolgen
docker-compose logs -f

# Einzelnen Service neustarten
docker-compose restart rag-service
```

### 4. Verfügbare Services
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **Backend Core**: http://localhost:8001
- **Auth Service**: http://localhost:8002
- **LLM Proxy**: http://localhost:8003
- **RAG Service**: http://localhost:8006
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Qdrant Vector DB**: http://localhost:6333

## 🔧 Entwicklungsumgebung

### Environment Variables
```bash
# .env.local aus Beispiel erstellen
cp .env.example .env.local

# API-Keys konfigurieren (erforderlich)
nano .env.local
```

**Wichtige Umgebungsvariablen:**
```bash
# Datenbank
DATABASE_URL=postgresql://user:password@localhost:5432/llm_frontend_db

# LLM Provider (mindestens einen für Chat)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

# Embedding Provider für RAG (erforderlich für RAG-Features)
OPENAI_EMBEDDING_API_KEY=sk-...  # Kann gleich wie OPENAI_API_KEY sein
RUNPOD_API_KEY=...               # Optional für RunPod Embeddings
EMBEDDING_PROVIDER=openai        # oder runpod
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# Qdrant Vector Database
QDRANT_HOST=vectordb
QDRANT_PORT=6333
QDRANT_COLLECTION=documents

# RAG Service Configuration
RAG_CHUNK_SIZE=1000
RAG_CHUNK_OVERLAP=200
RAG_MAX_CHUNKS=5

# JWT Security (in Produktion ändern!)
JWT_SECRET_KEY=your-secret-key-here

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
```

### Development Tools

#### Pre-commit Hooks
```bash
# Einmalige Einrichtung
./scripts/setup-precommit.sh

# Manuell ausführen
pre-commit run --all-files

# Hooks deaktivieren (nicht empfohlen)
git commit --no-verify
```

#### Code Quality
```bash
# Python
black --check .                 # Formatting
isort --check-only .            # Import sorting
flake8 .                        # Linting
bandit -r .                     # Security

# JavaScript/TypeScript
npm run lint:js                 # ESLint
npm run check:js                # Prettier check
npm run format:js               # Auto-format
```

#### Dependencies verwalten
```bash
# Alle Dependencies aktualisieren
./scripts/update-deps.sh

# Nur Python
source .venv/bin/activate
pip-compile --upgrade requirements.in

# Nur Node.js
npm update
```

## 🧪 Testing

### Unit Tests
```bash
# Alle Tests
npm run test

# Nur Python Tests
pytest backend-core/
pytest auth-service/
pytest rag-service/

# Mit Coverage
pytest --cov=. --cov-report=html
```

### Integration Tests
```bash
# Services starten und testen
docker-compose up -d
curl http://localhost:8080/health
curl http://localhost:8080/api/core/health
curl http://localhost:8080/api/rag/health

# RAG Service testen
curl http://localhost:8006/health
curl http://localhost:8006/collections
```

### RAG System Tests
```bash
# Document Upload Test
curl -X POST http://localhost:8006/documents \
  -F "file=@test.pdf" \
  -F "metadata={\"title\": \"Test Document\"}"

# Semantic Search Test
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "limit": 5}'

# RAG Query Test
curl -X POST http://localhost:8006/rag \
  -H "Content-Type: application/json" \
  -d '{"query": "What is this document about?"}'
```

## 🐳 Docker Development

### Services neu bauen
```bash
# Alle Services
docker-compose build

# RAG Service (häufig während Entwicklung)
docker-compose build rag-service

# Ohne Cache (bei Dependency-Änderungen)
docker-compose build --no-cache rag-service
```

### Debug Container
```bash
# In RAG Service Container einsteigen
docker-compose exec rag-service bash

# Qdrant Vector DB prüfen
docker-compose exec rag-service curl http://vectordb:6333/collections

# Logs eines Services
docker-compose logs -f rag-service
docker-compose logs -f vectordb

# Service neustarten
docker-compose restart rag-service
```

### Volumes verwalten
```bash
# Alle Daten löschen (Vorsicht!)
docker-compose down --volumes

# Nur Qdrant Daten löschen
docker volume rm llm-frontend_qdrant_data

# Volumes auflisten
docker volume ls | grep llm-frontend
```

## 🔍 Debugging

### Häufige Probleme

#### RAG Service startet nicht
```bash
# API-Keys prüfen
docker-compose logs rag-service | grep "API key"

# Qdrant-Verbindung prüfen
docker-compose exec rag-service curl http://vectordb:6333/collections

# Dependencies prüfen
docker-compose exec rag-service pip list | grep -E "(qdrant|httpx)"
```

#### Embedding API-Fehler
```bash
# API-Key Konfiguration prüfen
echo $OPENAI_EMBEDDING_API_KEY | head -c 20

# API-Verbindung testen
curl -H "Authorization: Bearer $OPENAI_EMBEDDING_API_KEY" \
  https://api.openai.com/v1/models

# RAG Service Logs prüfen
docker-compose logs rag-service | grep -E "(embedding|error)"
```

#### Qdrant Vector Database Issues
```bash
# Qdrant Status prüfen
curl http://localhost:6333/health

# Collections anzeigen
curl http://localhost:6333/collections

# Collection Details
curl http://localhost:6333/collections/documents

# Qdrant Logs prüfen
docker-compose logs vectordb
```

#### Port bereits belegt
```bash
# Prüfen welcher Prozess den Port nutzt
sudo lsof -i :8006  # RAG Service
sudo lsof -i :6333  # Qdrant
sudo lsof -i :3000  # Frontend

# Prozess beenden
sudo kill -9 <PID>
```

#### Datenbank-Verbindungsfehler
```bash
# Datenbank-Status prüfen
docker-compose exec postgres-db pg_isready -U user

# Verbindung testen
docker-compose exec postgres-db psql -U user -d llm_frontend_db -c "SELECT 1;"

# Logs prüfen
docker-compose logs postgres-db
```

#### Container startet nicht
```bash
# Detaillierte Logs
docker-compose logs --no-log-prefix <service-name>

# Build-Probleme prüfen
docker-compose build --no-cache <service-name>

# RAG Service Build prüfen
cd rag-service
docker build -t llm-frontend-rag .
```

### Logging & Monitoring

#### Strukturierte Logs
```bash
# RAG Service Logs
docker-compose logs -f rag-service | jq .

# Embedding API Calls verfolgen
docker-compose logs -f rag-service | grep embedding

# Qdrant Operations
docker-compose logs -f rag-service | grep qdrant
```

#### Health Checks
```bash
# Alle Service Health Checks
curl http://localhost:8080/health      # API Gateway
curl http://localhost:8001/health      # Backend Core
curl http://localhost:8002/health      # Auth Service
curl http://localhost:8003/health      # LLM Proxy
curl http://localhost:8006/health      # RAG Service
curl http://localhost:6333/health      # Qdrant

# RAG Service Status
curl http://localhost:8006/collections
curl http://localhost:8006/stats
```

#### Performance Monitoring
```bash
# Container-Ressourcen
docker stats

# RAG Service Performance
docker-compose exec rag-service python -c "
import psutil
print(f'Memory: {psutil.virtual_memory().percent}%')
print(f'CPU: {psutil.cpu_percent()}%')
"

# Qdrant Performance
curl http://localhost:6333/metrics
```

## 📦 Build & Deployment

### Production Build
```bash
# Production Images bauen
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Production starten
docker-compose -f docker-compose.prod.yml up -d

# RAG Service Production Config
export EMBEDDING_PROVIDER=openai
export LOG_LEVEL=WARNING
docker-compose -f docker-compose.prod.yml up -d rag-service
```

### Performance Optimizations (v0.13.0)
```bash
# Build Performance (84% Verbesserung)
docker-compose build --parallel

# Memory Optimization (50% Reduktion)
docker-compose up -d --scale rag-service=1

# Storage Optimization (50% Reduktion)
docker system prune -f
docker volume prune -f
```

## 🤖 RAG System Development

### Document Processing
```bash
# Unterstützte Formate
# PDF, TXT, MD, DOC, DOCX

# Upload Test
curl -X POST http://localhost:8006/documents \
  -F "file=@document.pdf" \
  -F "metadata={\"title\": \"Test\", \"category\": \"docs\"}"

# Batch Upload
for file in docs/*.pdf; do
  curl -X POST http://localhost:8006/documents \
    -F "file=@$file" \
    -F "metadata={\"title\": \"$(basename $file)\"}"
done
```

### Embedding Configuration
```bash
# OpenAI Embeddings (Standard)
export EMBEDDING_PROVIDER=openai
export OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# RunPod Embeddings (Alternative)
export EMBEDDING_PROVIDER=runpod
export RUNPOD_ENDPOINT=https://api.runpod.ai/v2/...

# Cost Tracking
curl http://localhost:8006/stats | jq .embedding_costs
```

### Vector Search Optimization
```bash
# Chunk-Größe optimieren
export RAG_CHUNK_SIZE=1000
export RAG_CHUNK_OVERLAP=200

# Search-Parameter tunen
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "search term",
    "limit": 10,
    "score_threshold": 0.7
  }'
```

## 📚 Code Conventions

### Python RAG Service
```python
# rag-service/main.py
import structlog
from typing import Dict, List, Optional
from fastapi import FastAPI, HTTPException

logger = structlog.get_logger(__name__)

async def process_document(
    file_content: bytes,
    metadata: Dict[str, Any]
) -> DocumentResponse:
    """Process uploaded document for RAG.
    
    Args:
        file_content: Raw document bytes
        metadata: Document metadata
        
    Returns:
        Document processing response
        
    Raises:
        ProcessingError: When document processing fails
    """
    logger.info("Processing document", 
                filename=metadata.get("filename"),
                size=len(file_content))
    
    # Chunking, Embedding, Storage
    return DocumentResponse(...)
```

### TypeScript Knowledge Base UI
```typescript
// frontend/src/components/KnowledgeBase.tsx
import React, { useState } from 'react';
import { DocumentUpload, SearchResult } from '@/types/rag';

interface KnowledgeBaseProps {
  onDocumentUpload: (doc: DocumentUpload) => Promise<void>;
  onSearch: (query: string) => Promise<SearchResult[]>;
}

export const KnowledgeBase: React.FC<KnowledgeBaseProps> = ({
  onDocumentUpload,
  onSearch
}) => {
  const [uploadCost, setUploadCost] = useState<number>(0);
  
  // Cost tracking integration
  const handleUpload = async (file: File) => {
    const response = await onDocumentUpload({ file });
    setUploadCost(response.embedding_cost);
  };
  
  return (
    <div className="knowledge-base">
      <DocumentUploader onUpload={handleUpload} />
      <CostTracker cost={uploadCost} />
      <SearchInterface onSearch={onSearch} />
    </div>
  );
};
```

## 🔒 Sicherheit

### API-Key Management
```bash
# API-Keys rotieren
export OPENAI_API_KEY=sk-new-key
docker-compose restart rag-service

# API-Key Encryption
python -c "
from cryptography.fernet import Fernet
key = Fernet.generate_key()
f = Fernet(key)
token = f.encrypt(b'sk-your-api-key')
print(f'Encrypted: {token}')
"
```

### RAG Security
```bash
# Document Upload Validation
curl -X POST http://localhost:8006/documents \
  -F "file=@malicious.exe"  # Should fail

# Query Sanitization
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{"query": "'; DROP TABLE documents; --"}'  # Should be sanitized
```

## 🤝 Beitragen

### RAG Development Workflow
```bash
# 1. RAG Feature Branch
git checkout -b feature/rag-enhancement

# 2. Development mit Hot Reload
docker-compose up -d --build rag-service

# 3. Tests ausführen
pytest rag-service/tests/

# 4. Performance Tests
curl -X POST http://localhost:8006/search \
  -H "Content-Type: application/json" \
  -d '{"query": "performance test", "limit": 100}'

# 5. Commit und Push
git add rag-service/
git commit -m "feat(rag): add semantic search enhancement"
git push origin feature/rag-enhancement
```

## 📞 Support

### RAG-spezifische Hilfe
```bash
# RAG Service Diagnostics
docker-compose exec rag-service python -c "
import qdrant_client
from rag_service.config import settings
print(f'Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}')
print(f'Provider: {settings.EMBEDDING_PROVIDER}')
"

# Embedding API Test
curl -X POST http://localhost:8006/embeddings/test \
  -H "Content-Type: application/json" \
  -d '{"text": "test embedding"}'
```

### Häufige RAG-Befehle
```bash
# RAG Service neustarten
docker-compose restart rag-service

# Qdrant Collection zurücksetzen
curl -X DELETE http://localhost:6333/collections/documents

# Embedding-Kosten prüfen
curl http://localhost:8006/stats | jq .total_costs

# Document-Index rebuilden
curl -X POST http://localhost:8006/admin/rebuild-index
```

---

**Letzte Aktualisierung:** 7. Juli 2025, 0:49 Uhr  
**Version:** v0.13.0 - Milestone 4.1 RAG & Vector Database abgeschlossen  
**Nächster Meilenstein:** 4.2 - Payment & Billing System 