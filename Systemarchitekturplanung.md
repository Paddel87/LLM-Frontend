# 🧩 Systemarchitekturplanung: KI-gestütztes Chat-Frontend für Multi-LLM-Nutzung

## 🎯 Vision & Zielsetzung

Ziel ist die Entwicklung einer vollständig selbst betriebenen Chat-Anwendung für Large Language Models (LLMs), die sich **funktional an TypingMind und AnythingLLM orientiert**, jedoch vollständig **Open Source** aufgebaut ist und keinerlei Verbindung zu externen Hersteller-Clouds nutzt.

Die Software soll:
- ein ansprechendes, intuitives UI im Stil von TypingMind haben,
- **mehrere LLMs via API oder RunPod/OpenRouter** einbinden können,
- vollständige Benutzerverwaltung, Tokenüberwachung und Abrechnung bieten,
- eine skalierbare, docker-compose-basierte Architektur nutzen,
- vollständig **lokale Datenhaltung** (PostgreSQL, Vektor-DB, optional S3) umsetzen,
- Storytelling & Role-Playing mit semantischer Speicherung unterstützen.

---

## 🔢 Geplante Systemmodule (12 Hauptmodule)

### 1. **User Interface (UI-Modul)**
- React-basiertes Frontend (Tailwind + Lucide Icons)
- Chat-UI wie bei TypingMind (Multi-Tab, Folder, Suchfunktion)
- Einfache, aber elegante Navigation (Dark-/Light-Mode)
- Lokale Speicherung vollständig deaktiviert – alles über zentrale Datenbank

### 2. **LLM-Anbindung**
- Anbindung über API-Keys an: OpenAI, Anthropic, Gemini, DeepSeek
- Optional über OpenRouter und RunPod-Modell
- Modellspezifische Parameter (z. B. Sicherheitsfunktionen) vollständig konfigurierbar
- Kompatibilitätsprüfung beim Modellwechsel (z. B. Kontextgröße)
- Tokenverbrauch pro Prompt (Input/Output) sichtbar + Kostenschätzung

### 3. **Datenhaltung & Backup**
- Alle Nutzerdaten, Chats, Einstellungen in gemeinsamer relationaler DB (PostgreSQL)
- Vektorbasierte Semantik mit Chroma oder Qdrant (embeddingfähig)
- Optional: Backup einzelner Chats/Projekte/Metadaten in S3-kompatibles Bucket

### 4. **Import & Migration**
- Import von bestehenden Chat-Frontends (z. B. ChatGPT.com, TypingMind)
- Übernahme von Ordnern, Verläufen, Dateianhängen

### 5. **Projektstruktur & Semantik**
- Jeder User kann Projekte in Ordnern organisieren
- Pro Ordner: mehrere Chats + Dateianhänge
- Einzelne Elemente können für RAG/Embedding semantisch gespeichert werden
- Freigaben für andere Benutzer möglich (Ordnerfreigabe durch Eigentümer)

### 6. **Vektordatenbank & RAG**
- Zentraler Vektorindex mit Trennung nach `user_id` und `project_id`
- Speicherung aller Embeddings durch Modul 5 (semantisch aktivierte Objekte)
- Such- und Retrieval-API für spätere RAG-Module

### 7. **Benutzerverwaltung & Rollen**
- Standard: Einzelbenutzermodus
- Optional: Multi-User mit isolierten Bereichen
- Rollen: `user`, `admin` (Vollzugriff, unsichtbar), (Projektmanager optional)
- Verschlüsselte API-Key-Speicherung pro Benutzer

### 8. **Tokenkosten & Modellkosten**
- Kosten pro Prompt dynamisch berechnet (inkl. Währungsauswahl)
- Automatisches Nachladen aktueller Preisdaten der Modelle
- Tokenlogging pro Anfrage

### 9. **Abrechnungssystem**
- Prepaid-System: nur wer Guthaben hat, darf kostenpflichtige Aktionen auslösen
- Preisaufschlag bei Nutzung bereitgestellter API-Keys (Margenfunktion)
- Keine kostenpflichtige Aktion über fremden API-Key ohne Guthaben

### 10. **Zahlungsabwicklung & Rechnungen**
- Abrechnung nur über Stripe (PayPal wird nicht unterstützt)
- Rechnungen mit USt. für Privat- und Geschäftskunden
- Stripe-Webhooks zur Aufladung / Rechnungserzeugung

### 11. **Projektdashboards & Verwaltungsfunktionen**
- Dashboard pro Projekt: verwendete Modelle, Tokenverbrauch, letzte Chats
- Projekte archivieren, duplizieren, importieren/exportieren

### 12. **Role-Playing & Storyelemente**
- Charaktere & Örtlichkeiten verwaltbar
- Bild-Upload (Portrait oder Ort)
- KI-Analyse: Generierung von Beschreibung anhand Bild (z. B. Haarfarbe, Raumgröße)
- Charaktere/Orte wiederverwendbar
- Fokus auf Langzeitkontext durch große Modelle (keine Tokenkarten notwendig)

---

## 🧱 Zielarchitektur (Docker Compose – Dev-Ebene)

**Containerübersicht:**

| Container            | Aufgabe                                  |
|----------------------|------------------------------------------|
| `frontend`           | UI (React + Tailwind)                    |
| `api-gateway`        | Schnittstelle für REST-Kommunikation     |
| `backend-core`       | Businesslogik, Projektverwaltung         |
| `auth-service`       | JWT/OAuth-basierte Authentifizierung     |
| `payment-service`    | Stripe-Integration                       |
| `llm-proxy`          | Anfragenrouting zu OpenAI, Gemini etc.   |
| `rag-service`        | Embedding + Vektorabfragen               |
| `postgres-db`        | Relationale Datenbank                    |
| `vectordb`           | Chroma oder Qdrant                       |

---

## 🔐 Sicherheitsvorgaben

- Alle sensiblen Daten verschlüsselt (insb. API-Keys)
- Keine Browser-Caching von Daten
- Trennung der Datenbereiche nach User und Projekt
- Admin hat vollen Zugriff (unsichtbar für andere)
- Auth über JWT (ggf. später OAuth2)

---

## 📌 Aufgabenstellung

Bitte entwickle eine vollständige **Systemarchitektur**, die:
- die obigen 12 Module **logisch miteinander verknüpft**,
- eine klare **Service-Kommunikation und Zuständigkeit** abbildet,
- geeignete **Datenflüsse und Schnittstellen** beschreibt (OpenAPI bevorzugt),
- das Deployment über **Docker Compose** umsetzbar macht,
- **später erweiterbar** ist (z. B. Installer, Cloud-Anbindung, RBAC etc.),
- eine **saubere Code-Trennung & Layerstruktur** (UI – API – Service – Data) definiert.

Ziel ist eine produktionsreife, modulare Architektur, auf deren Basis ein Open-Source-Projekt aufgebaut werden kann.

## 🧪 Entwicklungsumgebung

- Python 3.x (empfohlen: 3.11+)
- Virtuelle Umgebung via `python -m venv .venv`
- Aktivierung:  
  - Unix/Mac: `source .venv/bin/activate`  
  - Windows: `.venv\Scripts\activate`
- Abhängigkeiten: `pip install -r requirements.txt`
