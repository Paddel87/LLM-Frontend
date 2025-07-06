# 🤖 LLM-Frontend - Open Source Multi-LLM Chat Interface

<p align="center">
  <img src="https://img.shields.io/badge/version-0.5.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/status-phase%201%20complete-brightgreen.svg" alt="Status">
  <img src="https://img.shields.io/badge/docker-ready-blue.svg" alt="Docker">
  <img src="https://img.shields.io/github/last-commit/Paddel87/LLM-Frontend" alt="Last Commit">
</p>

## 🎯 Über das Projekt

**LLM-Frontend** ist eine selbst-hostbare, Open-Source Alternative zu kommerziellen LLM-Chat-Interfaces wie TypingMind oder AnythingLLM. Das Projekt bietet vollständige Datensouveränität und ermöglicht die Nutzung mehrerer Large Language Models über eine einheitliche, moderne Benutzeroberfläche.

> **📊 Status Update:** Phase 1 (Fundament & Infrastruktur) erfolgreich abgeschlossen! ✅  
> Vollständiges Datenbankschema, JWT-Authentication und Core API Gateway implementiert.  
> **Bereit für Phase 2:** Backend Core Services & LLM Integration

### ✨ Hauptfeatures

- 🔌 **Multi-LLM Support**: OpenAI, Anthropic, Google Gemini, DeepSeek, OpenRouter, RunPod
- 👥 **Multi-User System**: Vollständige Benutzerverwaltung mit Rollen und Berechtigungen
- 💳 **Integriertes Bezahlsystem**: Prepaid-System mit Stripe-Integration
- 📊 **Token-Tracking**: Echtzeit-Überwachung von Kosten und Verbrauch
- 🗂️ **Projekt-Organisation**: Ordnerstruktur für Chats und Dokumente
- 🤖 **RAG-Unterstützung**: Semantische Suche mit Vektordatenbank
- 🎭 **Role-Playing Features**: Charaktere und Story-Management
- 🔒 **100% Privatsphäre**: Keine externen Abhängigkeiten, vollständige Kontrolle

## 🚀 Schnellstart

### Voraussetzungen

- Docker & Docker Compose (v2.0+)
- 8GB RAM minimum
- 20GB freier Speicherplatz

### Installation (2 Minuten)

```bash
# Repository klonen
git clone https://github.com/Paddel87/LLM-Frontend.git
cd LLM-Frontend

# Automatisches Setup (alles in einem Befehl)
./scripts/dev-setup.sh

# Services starten
docker-compose up -d

# 🎉 Fertig! Öffne http://localhost:3000
```

### Alternative: Manuelle Installation

```bash
# Umgebungsvariablen konfigurieren
cp .env.example .env.local
# Editiere .env.local mit deinen API-Keys

# Services starten
docker-compose up -d
```

### Erste Schritte

1. **Registrierung**: Erstelle einen Admin-Account beim ersten Start
2. **API-Keys**: Füge deine LLM-API-Keys in den Einstellungen hinzu
3. **Projekt erstellen**: Organisiere deine Chats in Projekten
4. **Chatten**: Wähle ein Modell und starte deine erste Unterhaltung

## 🏗️ Architektur

Das System basiert auf einer Microservice-Architektur mit folgenden Komponenten:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│  API Gateway │────▶│   Services  │
│   (React)   │     │   (Express)  │     │  (FastAPI)  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │
                    ┌───────┴────────┐
                    │                │
              ┌─────▼─────┐   ┌─────▼─────┐
              │PostgreSQL │   │  Qdrant   │
              │    DB     │   │ VectorDB  │
              └───────────┘   └───────────┘
```

### Services

- **Frontend**: React + TypeScript + Tailwind CSS
- **API Gateway**: Request-Routing und Load Balancing
- **Auth Service**: JWT-basierte Authentifizierung
- **Backend Core**: Projekt- und Chat-Management
- **LLM Proxy**: Abstraktion für verschiedene LLM-Provider
- **RAG Service**: Embedding und semantische Suche
- **Payment Service**: Stripe-Integration und Abrechnung

## 📖 Dokumentation

### Für Nutzer
- [Benutzerhandbuch](docs/user-guide.md)
- [FAQ](docs/faq.md)
- [Troubleshooting](docs/troubleshooting.md)

### Für Entwickler
- [Entwicklungsumgebung einrichten](docs/development.md)
- [API-Dokumentation](docs/api.md)
- [Architektur-Übersicht](docs/architecture.md)
- [Contributing Guidelines](CONTRIBUTING.md)

### Für Administratoren
- [Installation & Deployment](docs/deployment.md)
- [Konfiguration](docs/configuration.md)
- [Backup & Recovery](docs/backup.md)
- [Monitoring](docs/monitoring.md)

## 🔧 Konfiguration

### Umgebungsvariablen

```env
# Datenbank
DATABASE_URL=postgresql://user:password@postgres:5432/llm_frontend
REDIS_URL=redis://redis:6379

# Sicherheit
JWT_SECRET=your-secret-key
ENCRYPTION_KEY=your-encryption-key

# LLM API Keys (optional - Nutzer können eigene Keys verwenden)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...

# Payment
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# S3 Storage (optional)
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=minioadmin
S3_SECRET_KEY=minioadmin
```

## 🛠️ Entwicklung

### Lokale Entwicklung

```bash
# Backend-Services
cd backend-core
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload

# Frontend
cd frontend
npm install
npm run dev
```

### Tests ausführen

```bash
# Backend Tests
pytest

# Frontend Tests
npm test

# E2E Tests
npm run test:e2e
```

### Code-Qualität

```bash
# Python Linting
flake8 .
black .

# Frontend Linting
npm run lint
npm run format
```

## 🤝 Beitragen

Wir freuen uns über Beiträge! Bitte lies unsere [Contributing Guidelines](CONTRIBUTING.md) für Details.

### Entwicklungsprozess

1. Fork das Repository
2. Erstelle einen Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Committe deine Änderungen (`git commit -m 'Add some AmazingFeature'`)
4. Push zum Branch (`git push origin feature/AmazingFeature`)
5. Öffne einen Pull Request

### Code of Conduct

Dieses Projekt folgt dem [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md).

## 📊 Projekt-Status

- **Aktuelle Version**: 0.5.0 ✅ **Phase 1 abgeschlossen**
- **Entwicklungsstand**: Bereit für Phase 2 (Backend Core Services)
- **Roadmap**: Siehe [ROADMAP.md](ROADMAP.md)
- **Changelog**: Siehe [CHANGELOG.md](CHANGELOG.md)

### ✅ Abgeschlossen (Phase 0 + 1)

- [x] **Phase 0:** Vollständige Entwicklungsumgebung
- [x] **Phase 0:** CI/CD-Pipeline mit GitHub Actions
- [x] **Phase 0:** Code-Quality-System (Linting, Testing)
- [x] **Phase 0:** Strukturiertes Logging-Framework
- [x] **Phase 0:** Docker Compose Setup mit Hot-Reload
- [x] **Phase 0:** Umfassende Dokumentation
- [x] **Phase 1:** Datenbankschema & ERD (13 Tabellen)
- [x] **Phase 1:** Alembic Migrationen & SQLAlchemy Models
- [x] **Phase 1:** JWT-basierte Authentifizierung (580+ Zeilen)
- [x] **Phase 1:** User Management (Register, Login, Profile)
- [x] **Phase 1:** API Gateway mit OpenAPI 3.0 (445+ Zeilen)
- [x] **Phase 1:** Rate Limiting, CORS, Health Checks
- [x] **Phase 1:** Comprehensive Security Implementation

### 🚀 Nächste Phase (Phase 2)

- [ ] Project & Chat Management APIs
- [ ] LLM Proxy Service (Multi-Provider Support)
- [ ] Data Import/Export Tools
- [ ] Token Counting & Cost Calculation
- [ ] Streaming Support for LLM Responses

## 🔐 Sicherheit

- Alle API-Keys werden verschlüsselt gespeichert
- JWT-basierte Authentifizierung
- Rate Limiting auf allen Endpoints
- Regelmäßige Security Audits

Sicherheitslücken bitte an: security@llm-frontend.example

## 📜 Lizenz

Dieses Projekt ist unter der MIT-Lizenz lizenziert - siehe [LICENSE](LICENSE) für Details.

## 🙏 Credits

### Technologien

- [FastAPI](https://fastapi.tiangolo.com/)
- [React](https://reactjs.org/)
- [Tailwind CSS](https://tailwindcss.com/)
- [PostgreSQL](https://www.postgresql.org/)
- [Qdrant](https://qdrant.tech/)

### Inspiration

Dieses Projekt wurde inspiriert von:
- [TypingMind](https://typingmind.com/)
- [AnythingLLM](https://anythingllm.com/)
- [ChatGPT](https://chat.openai.com/)

## 📞 Support & Kontakt

- **GitHub Issues**: [Bugs & Feature Requests](https://github.com/yourusername/llm-frontend/issues)
- **Discussions**: [Community Forum](https://github.com/yourusername/llm-frontend/discussions)
- **Discord**: [Join our Discord](https://discord.gg/llm-frontend)
- **Email**: support@llm-frontend.example

---

<p align="center">
  Made with ❤️ by the Open Source Community
</p> 