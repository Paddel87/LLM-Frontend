# 🛠️ LLM-Frontend Entwicklungsanleitung

## 📋 Übersicht

Dieses Dokument beschreibt die Einrichtung und Entwicklung des **LLM-Frontend** Projekts. Das System besteht aus mehreren Microservices, die über Docker Compose orchestriert werden.

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
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  Payment Svc    │  │   LLM Proxy     │  │   RAG Service   │
│  (FastAPI)      │  │   (FastAPI)     │  │   (FastAPI)     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
        │                     │                     │
        ▼                     ▼                     ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │   AI Providers  │  │     Qdrant      │
│   (Database)    │  │ (OpenAI, etc.)  │  │ (Vector Store)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

## 🔧 Systemvoraussetzungen

### Minimal Requirements
- **Docker**: >= 24.0
- **Docker Compose**: >= 2.20
- **Git**: >= 2.30
- **Node.js**: >= 18.0 (für lokale Entwicklung)
- **Python**: >= 3.11 (für lokale Entwicklung)

### Empfohlene Systemspezifikationen
- **RAM**: 8GB+ (16GB empfohlen)
- **CPU**: 4+ Kerne
- **Disk**: 20GB+ freier Speicherplatz
- **OS**: Linux, macOS, oder Windows mit WSL2

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
docker-compose restart backend-core
```

### 4. Verfügbare Services
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8080
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379
- **Qdrant**: http://localhost:6333

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

# LLM Provider (mindestens einen)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_API_KEY=AI...

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

# Mit Coverage
pytest --cov=. --cov-report=html
```

### Integration Tests
```bash
# Services starten und testen
docker-compose up -d
curl http://localhost:8080/health
curl http://localhost:8080/api/core/
```

### End-to-End Tests
```bash
# TODO: E2E Tests implementieren
# npm run test:e2e
```

## 🐳 Docker Development

### Services neu bauen
```bash
# Alle Services
docker-compose build

# Einzelner Service
docker-compose build backend-core

# Ohne Cache
docker-compose build --no-cache
```

### Debug Container
```bash
# In Container einsteigen
docker-compose exec backend-core bash
docker-compose exec postgres-db psql -U user -d llm_frontend_db

# Logs eines Services
docker-compose logs -f backend-core

# Service neustarten
docker-compose restart auth-service
```

### Volumes verwalten
```bash
# Datenbank-Daten löschen
docker-compose down --volumes

# Volumes auflisten
docker volume ls

# Bestimmtes Volume löschen
docker volume rm llm-frontend_postgres_data
```

## 🔍 Debugging

### Häufige Probleme

#### Port bereits belegt
```bash
# Prüfen welcher Prozess den Port nutzt
sudo lsof -i :8080
sudo lsof -i :3000

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

# Image manuell bauen
cd <service-dir>
docker build -t llm-frontend-<service> .
```

#### Python Import-Fehler
```bash
# Virtual Environment aktivieren
source .venv/bin/activate

# Dependencies installieren
pip install -r requirements-dev.txt
pip install -r backend-core/requirements.txt

# Python-Pfad prüfen
python -c "import sys; print(sys.path)"
```

#### Node.js Module-Fehler
```bash
# Node modules neu installieren
rm -rf node_modules package-lock.json
npm install

# Cache leeren
npm cache clean --force

# Node Version prüfen
node --version
npm --version
```

### Logging & Monitoring

#### Strukturierte Logs
```bash
# Alle Services
docker-compose logs -f --tail=100

# JSON-Format für Produktion
export LOG_FORMAT=json
docker-compose up -d

# Logs nach Service filtern
docker-compose logs -f backend-core | jq .
```

#### Health Checks
```bash
# Automatische Health Checks
curl http://localhost:8080/health
curl http://localhost:8080/api/core/health
curl http://localhost:8080/api/auth/health

# Service-Status
docker-compose ps
```

#### Performance Monitoring
```bash
# Container-Ressourcen
docker stats

# Datenbank-Performance
docker-compose exec postgres-db psql -U user -d llm_frontend_db -c "
  SELECT * FROM pg_stat_activity WHERE state = 'active';
"
```

## 📦 Build & Deployment

### Production Build
```bash
# Production Images bauen
docker-compose -f docker-compose.yml -f docker-compose.prod.yml build

# Production starten
docker-compose -f docker-compose.prod.yml up -d
```

### Release Process
```bash
# Version Tag erstellen
git tag v0.1.0
git push origin v0.1.0

# Automatischer Release via GitHub Actions
# (siehe .github/workflows/release.yml)
```

## 🔒 Sicherheit

### Secrets Management
```bash
# Secrets scannen
detect-secrets scan --baseline .secrets.baseline

# Baseline aktualisieren
detect-secrets scan --update .secrets.baseline

# Pre-commit Hook für Secrets
pre-commit run detect-secrets --all-files
```

### Security Audit
```bash
# Python Dependencies
safety check

# Node.js Dependencies
npm audit

# Docker Images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image llm-frontend-backend-core
```

## 📚 Code Conventions

### Python (PEP 8 + Black)
```python
# Imports
from typing import Dict, List, Optional
import structlog

# Logging
logger = structlog.get_logger(__name__)

# Functions
def process_user_data(
    user_id: int,
    data: Dict[str, Any],
    options: Optional[Dict[str, Any]] = None
) -> UserResponse:
    """Process user data with validation.
    
    Args:
        user_id: Unique user identifier
        data: User data dictionary
        options: Optional processing options
        
    Returns:
        Processed user response
        
    Raises:
        ValidationError: When data is invalid
    """
    logger.info("Processing user data", user_id=user_id)
    # Implementation
```

### JavaScript/TypeScript
```typescript
// Imports (sorted by ESLint)
import React, { useState, useEffect } from 'react';
import { UserData, ApiResponse } from '@/types';

// Components
interface UserProps {
  userId: string;
  onUpdate: (data: UserData) => void;
}

export const UserComponent: React.FC<UserProps> = ({ 
  userId, 
  onUpdate 
}) => {
  const [userData, setUserData] = useState<UserData | null>(null);
  
  // Implementation
};
```

### Git Commit Messages
```bash
# Format: <type>(<scope>): <description>
git commit -m "feat(auth): add JWT token validation"
git commit -m "fix(docker): resolve container startup issue"
git commit -m "docs(api): update OpenAPI specification"

# Types: feat, fix, docs, style, refactor, test, chore
# Scopes: auth, api, frontend, docker, ci
```

## 🤝 Beitragen

### Development Workflow
```bash
# 1. Branch erstellen
git checkout -b feature/new-feature

# 2. Entwicklung
# ... Code ändern ...

# 3. Tests ausführen
npm run test
pre-commit run --all-files

# 4. Commit
git add .
git commit -m "feat: add new feature"

# 5. Push und Pull Request
git push origin feature/new-feature
```

### Pull Request Checklist
- [ ] Tests passieren
- [ ] Pre-commit Hooks erfolgreich
- [ ] Dokumentation aktualisiert
- [ ] Breaking Changes dokumentiert
- [ ] Security Review (falls nötig)

## 📞 Support

### Dokumentation
- **README.md**: Projektübersicht
- **ROADMAP.md**: Entwicklungsplan
- **CHANGELOG.md**: Versionshistorie

### Hilfe erhalten
- **GitHub Issues**: Bugs und Feature Requests
- **GitHub Discussions**: Fragen und Diskussionen
- **Discord**: Community Chat (Link folgt)

### Häufige Befehle
```bash
# Entwicklung starten
./scripts/dev-setup.sh && docker-compose up -d

# Code formatieren
npm run format && pre-commit run --all-files

# Dependencies aktualisieren
./scripts/update-deps.sh

# Vollständiger Reset
docker-compose down --volumes && docker system prune -f
```

---

**Letzte Aktualisierung:** Juli 2025  
**Version:** v0.1.0 