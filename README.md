# 🤖 LLM-Frontend - Open Source Multi-LLM Chat Interface

<p align="center">
  <img src="https://img.shields.io/badge/version-0.1.0-blue.svg" alt="Version">
  <img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.11+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/status-development-orange.svg" alt="Status">
</p>

## 🎯 Über das Projekt

**LLM-Frontend** ist eine selbst-hostbare, Open-Source Alternative zu kommerziellen LLM-Chat-Interfaces wie TypingMind oder AnythingLLM. Das Projekt bietet vollständige Datensouveränität und ermöglicht die Nutzung mehrerer Large Language Models über eine einheitliche, moderne Benutzeroberfläche.

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

### Installation (5 Minuten)

```bash
# Repository klonen
git clone https://github.com/yourusername/llm-frontend.git
cd llm-frontend

# Umgebungsvariablen konfigurieren
cp .env.example .env
# Editiere .env mit deinen API-Keys und Einstellungen

# Services starten
docker-compose up -d

# Frontend öffnen
# http://localhost:3000
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

- **Aktuelle Version**: 0.1.0 (Early Development)
- **Roadmap**: Siehe [ROADMAP.md](ROADMAP.md)
- **Changelog**: Siehe [CHANGELOG.md](CHANGELOG.md)

### Geplante Features

- [ ] Mobile App (iOS/Android)
- [ ] Voice Input/Output
- [ ] Plugin-System
- [ ] Kubernetes Deployment
- [ ] Multi-Language Support

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