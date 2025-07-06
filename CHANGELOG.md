# 📝 Changelog

Alle nennenswerten Änderungen an diesem Projekt werden in dieser Datei dokumentiert.

Das Format basiert auf [Keep a Changelog](https://keepachangelog.com/de/1.0.0/),
und dieses Projekt verwendet [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### 🎯 Geplant
- Multi-Language Support (i18n)
- Plugin-System
- Mobile Apps (iOS/Android)
- Voice Input/Output
- Kubernetes Deployment Manifests

---

## [0.8.0] - 2025-07-06

### 🎉 Phase 2 Abgeschlossen - Backend Core Services
- Vollständige Backend-APIs mit Project & Chat Management
- LLM Proxy Service mit 6 Provider-Integrations
- Import/Export Tools für ChatGPT und TypingMind
- Token Counting & Cost Calculation System
- Streaming Support für alle LLM-Provider

### ✨ Added
- **Project & Chat Management (Milestone 2.1)**
  - Backend-Core Service erweitert (1200+ Zeilen)
  - CRUD APIs für Projects, Folders, Chats, Messages
  - Pydantic Request/Response Models
  - Hierarchical Folder Structure mit Validation
  - Search & Filter Functions (Content-basiert)
  - Batch Operations (Bulk Archiving)
  - JWT Authentication Dependencies
  - SQLAlchemy Integration mit existierenden Models

- **LLM Proxy Service (Milestone 2.2)**
  - LLM-Proxy Service kompletter Rewrite (1000+ Zeilen)
  - **6 LLM Provider integriert:**
    - OpenAI (GPT-4, GPT-3.5-turbo)
    - Anthropic (Claude-3-Sonnet, Claude-3-Haiku)
    - Google (Gemini-Pro)
    - DeepSeek (DeepSeek-Chat)
    - OpenRouter (Multi-model support)
    - RunPod (Custom endpoints)
  - Provider Abstraction Layer mit Base-Class
  - Token Counting mit tiktoken für alle Provider
  - Cost Calculation mit aktuellen Preisen
  - Streaming Support mit Server-Sent Events
  - Comprehensive Error Handling & Retry Logic
  - Model Configurations mit Pricing Data

- **Data Import/Export (Milestone 2.3)**
  - ChatGPT Export Parser (JSON Format)
  - TypingMind Import Funktionalität
  - Export Formats: JSON, Markdown, CSV, TXT
  - Bulk Import API für multiple Formate
  - File Attachment Migration System
  - Data Validation & Parsing

### 🔧 Technical Infrastructure
- **Requirements Updates**: Alle Services mit spezifischen Versionen
- **Docker Compose Enhancement**: Vollständige Entwicklungsumgebung mit:
  - Backend Services (API Gateway, Backend-Core, LLM-Proxy, Auth-Service)
  - Database Services (PostgreSQL, Redis)
  - Development Tools (pgAdmin, Redis Commander)
  - Monitoring Services (Prometheus, Grafana)
- **Environment Configuration**: `env.example` mit LLM Provider API Keys
- **Code Quality**: Alle Python-Dateien kompilieren erfolgreich

### 📦 Dependencies Added
- **Backend**: tiktoken, openai, anthropic, google-generativeai
- **HTTP Clients**: httpx, requests mit async support
- **Data Processing**: pandas, python-multipart
- **LLM Integration**: Provider-spezifische SDKs
- **Development**: Comprehensive monitoring stack

### 🚀 Ready for Phase 3
- Vollständige Backend-Infrastruktur
- LLM-Integration mit 6 Providern
- Import/Export Capabilities
- Token Counting & Cost Tracking
- Streaming Support für Real-time Responses
- Containerized Services für Development/Production

---

## [0.5.0] - 2025-07-06

### 🎉 Phase 1 Abgeschlossen - Fundament & Infrastruktur
- Vollständiges Datenbankschema mit 13 Tabellen implementiert
- JWT-basierte Authentifizierung mit User Management
- Core API Gateway mit OpenAPI 3.0 Spezifikation
- Umfassende Sicherheits- und Monitoring-Features

### ✨ Added
- **Database Schema (Milestone 1.1)**
  - 13-Tabellen PostgreSQL Schema (528 Zeilen)
  - Vollständige ERD-Dokumentation
  - Alembic Migrationen Setup
  - SQLAlchemy Models (434 Zeilen)
  - Indizes, Trigger, Views und Stored Procedures
  - User/Role/Permission System
  - Project/Folder/Chat/Message Structure
  - API Keys & Token Management
  - Usage Tracking & Payment System

- **Authentication & Authorization (Milestone 1.2)**
  - JWT-basierte Authentifizierung (580+ Zeilen)
  - User Registration mit Email-Verifizierung
  - Login/Logout mit Token-Management
  - Password Reset & Change Funktionalität
  - API-Key Management (verschlüsselt)
  - Role-Based Access Control (RBAC)
  - Session Management mit Refresh Tokens
  - Admin-Endpoints für Token-Cleanup

- **Core API Gateway (Milestone 1.3)**
  - OpenAPI 3.0 Spezifikation (445 Zeilen)
  - Swagger UI Documentation unter `/docs`
  - Express.js Gateway mit Rate Limiting
  - CORS-Konfiguration für Dev/Production
  - Comprehensive Health Checks
  - Security Middleware (Helmet, Compression)
  - API Versioning (`/api/v1/`)
  - Service Proxy für alle Microservices
  - Request/Response Logging mit Request-IDs

### 🔧 Technical Infrastructure
- **Database**: PostgreSQL Schema mit 13 Tabellen
- **Security**: JWT Tokens, bcrypt Password Hashing, API Key Encryption
- **API**: OpenAPI 3.0 mit vollständiger Dokumentation
- **Monitoring**: Health Checks, Service Status, Uptime Tracking
- **Error Handling**: Strukturierte Fehlerbehandlung mit HTTP Status Codes

### 📦 Dependencies Added
- **Backend**: SQLAlchemy, Alembic, python-jose, passlib, bcrypt
- **API Gateway**: express, swagger-ui-express, helmet, compression
- **Security**: express-rate-limit, cors, http-proxy-middleware
- **Logging**: winston, structlog für Request-Tracking

### 🛠️ Database Schema
- `users` - User accounts with roles
- `roles` & `permissions` - RBAC system
- `projects` & `folders` - Project organization
- `chats` & `messages` - Chat management
- `api_keys` & `tokens` - Security management
- `usage_logs` - Cost tracking
- `payments` & `invoices` - Billing system
- `user_balance` - Account balance tracking

### 🚀 Ready for Phase 2
- Vollständiges Backend-Fundament
- Sichere Authentifizierung
- API-Gateway mit Dokumentation
- Datenbankschema für alle Features
- Monitoring & Health Checks

---

## [0.2.0] - 2025-07-06

### 🎉 Phase 0 Abgeschlossen - Projektinitialisierung
- Vollständige Entwicklungsumgebung eingerichtet
- Automatisierte Code-Quality-Checks implementiert
- Sichere CI/CD-Pipeline aufgebaut
- Umfassende Dokumentation erstellt

### ✨ Added
- **Development Environment**
  - `.gitignore` für Python, Node.js, Docker, IDEs
  - Umgebungsvariablen-System mit `.env.example` (80+ Variablen)
  - Strukturiertes JSON-Logging mit `structlog` und Winston
  - Hot-Reload Docker Compose Setup
  - Development-Tools Container (pgAdmin, Mailhog, Redis Commander)

- **Code Quality & CI/CD**
  - Pre-commit Hooks mit vollständiger Linting-Pipeline
  - Python: Black, isort, flake8, bandit, mypy
  - JavaScript: ESLint, Prettier mit TypeScript Support
  - GitHub Actions CI/CD Pipeline
  - Automatisierte Docker Image Builds
  - CodeQL Security Analysis
  - Dependabot für automatische Updates

- **Dependency Management**
  - `pip-tools` für Python-Paketmanagement
  - `requirements.in` Dateien für alle Services
  - Automatisches Update-Script (`scripts/update-deps.sh`)
  - Security-Audit Integration
  - Zentrale Development-Dependencies

- **Scripts & Automation**
  - `scripts/dev-setup.sh` - Vollständiges Setup mit einem Befehl
  - `scripts/setup-precommit.sh` - Pre-commit Hooks Installation
  - `scripts/update-deps.sh` - Dependency-Management
  - `scripts/init.sql` - Datenbank-Setup

- **Documentation**
  - `DEVELOPMENT.md` - Umfassende Entwicklungsanleitung
  - Setup-Anleitungen mit Troubleshooting
  - Code Conventions und Best Practices
  - Docker-Debugging Guides

### 🔧 Technical Infrastructure
- **Logging**: Request-ID Tracing zwischen Services
- **Docker**: Multi-stage builds, health checks, development tools
- **GitHub Actions**: Matrix builds, security scanning, automated releases
- **Security**: Secrets detection, vulnerability scanning, audit logging

### 📦 Dependencies Updated
- **Python Services**: FastAPI, SQLAlchemy, strukturiertes Logging
- **Development Tools**: pytest, mypy, black, isort, flake8, bandit
- **Node.js**: Winston, ESLint, Prettier, npm-run-all
- **CI/CD**: GitHub Actions, CodeQL, Dependabot

### 🛠️ Configuration Files
- `.pre-commit-config.yaml` - Pre-commit Hooks
- `.flake8`, `.bandit`, `.yamllint` - Python Linting
- `.eslintrc.js`, `.prettierrc.js` - JavaScript Linting
- `package.json` - Root-level Dependencies
- `requirements-dev.txt` - Development Dependencies

### 🚀 Ready for Phase 1
- Vollständige Entwicklungsumgebung
- Automatisierte Code-Quality-Checks
- Sichere CI/CD-Pipeline
- Umfassende Dokumentation
- Strukturiertes Logging
- Dependency Management

---

## [0.1.0] - 2025-07-06

### 🎉 Initial Release
- Projektinitialisierung und Grundstruktur
- Docker Compose Setup für alle Services
- Basis-Skelett für Microservices
- Cursor Rules definiert
- Entwicklungs-Roadmap erstellt

### ✨ Added
- **Infrastructure**
  - Docker Compose Konfiguration
  - Service-Definitionen (9 Container)
  - PostgreSQL und Qdrant Integration
  - API Gateway mit Express.js

- **Services (Grundgerüst)**
  - Auth Service (FastAPI)
  - Backend Core (FastAPI)
  - LLM Proxy (FastAPI)
  - Payment Service (FastAPI)
  - RAG Service (FastAPI)

- **Frontend**
  - React Setup mit Tailwind CSS
  - Basis-Komponenten
  - Lucide Icons Integration

- **Dokumentation**
  - README.md für Projektübersicht
  - ROADMAP.md mit Entwicklungsplan
  - CHANGELOG.md mit Versionierung
  - Systemarchitekturplanung.md

### 🔧 Technical Details
- Python 3.11+ für Backend Services
- React 18 für Frontend
- PostgreSQL 15 für Datenhaltung
- Qdrant für Vektordatenbank
- FastAPI für alle Python Services
- Express.js für API Gateway

### 📦 Dependencies
- Backend: FastAPI, SQLAlchemy, Pydantic
- Frontend: React, Tailwind CSS, Lucide-React
- Infrastructure: Docker, Docker Compose

---

## Versionsschema

### Semantic Versioning
- **MAJOR (X.0.0)**: Inkompatible API-Änderungen
- **MINOR (0.X.0)**: Neue Features (rückwärtskompatibel)
- **PATCH (0.0.X)**: Bugfixes (rückwärtskompatibel)

### Pre-Release Versionen
- **Alpha**: 0.x.x-alpha.n (Frühe Entwicklung)
- **Beta**: 0.x.x-beta.n (Feature-Complete, Testing)
- **RC**: 0.x.x-rc.n (Release Candidate)

### Version Tags
- `latest` - Aktuellste stabile Version
- `develop` - Aktueller Entwicklungsstand
- `experimental` - Experimentelle Features

---

## Kommende Versionen (Geplant)

### [0.2.0] - ✅ Abgeschlossen - Projektinitialisierung
- ✅ Umgebungsvariablen-System
- ✅ Logging-Framework
- ✅ CI/CD Pipeline
- ✅ Development Tools

### [0.3.0] - Datenbankschema
- PostgreSQL Schema
- Alembic Migrationen
- Basis-Modelle
- Seed-Daten

### [0.4.0] - Authentication
- JWT Implementation
- User Registration/Login
- API-Key Management
- RBAC System

### [0.5.0] - Core API
- OpenAPI Spezifikation
- CRUD Operations
- Error Handling
- API Versionierung

### [0.6.0] - Project Management
- Projekt CRUD APIs
- Ordnerstruktur
- Chat-Sessions
- Metadaten

### [0.7.0] - LLM Integration
- Provider Abstraktion
- Token Counting
- Streaming Support
- Error Handling

### [0.8.0] - Import/Export
- ChatGPT Import
- TypingMind Import
- Export Funktionen
- Bulk Operations

### [0.9.0] - Frontend Foundation
- TypeScript Migration
- Component Library
- Dark/Light Mode
- Responsive Design

### [0.10.0] - Authentication UI
- Login/Register Forms
- Password Reset
- Profile Settings
- API-Key UI

### [0.11.0] - Chat Interface
- Multi-Tab Support
- Markdown Rendering
- Code Highlighting
- Model Switcher

### [0.12.0] - Project UI
- Dashboard
- Tree Navigation
- Drag & Drop
- Search

### [1.0.0] - Production Release
- Feature Complete
- Fully Tested
- Documentation
- Deployment Ready

---

## Support-Zeiträume

| Version | Status | Support Ende |
|---------|---------|--------------|
| 1.x.x | LTS | 2027-12-31 |
| 0.x.x | Development | 2025-12-31 |

---

## Links

- [GitHub Releases](https://github.com/yourusername/llm-frontend/releases)
- [Upgrade Guide](docs/upgrade.md)
- [Migration Guide](docs/migration.md)

---

**Hinweis**: Dieses Changelog wird bei jeder neuen Version aktualisiert. Für detaillierte Commit-Historie siehe GitHub. 