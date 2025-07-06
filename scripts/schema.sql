-- ===================================================
-- LLM-Frontend Vollständiges Datenbankschema
-- Phase 1.1: Erweiterte Tabellen für Produktion
-- ===================================================

-- Erweiterungen aktivieren
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ===================================================
-- BENUTZER & AUTHENTIFIZIERUNG
-- ===================================================

-- Benutzer-Tabelle
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    is_admin BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    last_login TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollen-Tabelle
CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Benutzer-Rollen-Zuordnung
CREATE TABLE user_roles (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);

-- Berechtigungen
CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    resource VARCHAR(50) NOT NULL,
    action VARCHAR(50) NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rollen-Berechtigungen-Zuordnung
CREATE TABLE role_permissions (
    role_id INTEGER REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INTEGER REFERENCES permissions(id) ON DELETE CASCADE,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (role_id, permission_id)
);

-- ===================================================
-- PROJEKT & ORDNER-STRUKTUR
-- ===================================================

-- Projekte-Tabelle
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    owner_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    is_shared BOOLEAN DEFAULT FALSE,
    color VARCHAR(7) DEFAULT '#3B82F6',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Ordner-Tabelle (hierarchische Struktur)
CREATE TABLE folders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    parent_folder_id INTEGER REFERENCES folders(id) ON DELETE CASCADE,
    color VARCHAR(7) DEFAULT '#6B7280',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- CHAT & NACHRICHTEN
-- ===================================================

-- Chats-Tabelle
CREATE TABLE chats (
    id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    folder_id INTEGER REFERENCES folders(id) ON DELETE SET NULL,
    model_name VARCHAR(100),
    system_prompt TEXT,
    model_config JSONB DEFAULT '{}',
    temperature DECIMAL(3,2) DEFAULT 0.7,
    max_tokens INTEGER DEFAULT 4000,
    is_archived BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Nachrichten-Tabelle
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    token_count INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0.00,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- API-SCHLÜSSEL & TOKENS
-- ===================================================

-- API-Schlüssel (verschlüsselt)
CREATE TABLE api_keys (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    key_hash VARCHAR(255) NOT NULL,
    key_name VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP
);

-- JWT & Session Tokens
CREATE TABLE tokens (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    token_hash VARCHAR(255) NOT NULL,
    token_type VARCHAR(50) NOT NULL CHECK (token_type IN ('access', 'refresh', 'api', 'email_verification', 'password_reset')),
    expires_at TIMESTAMP NOT NULL,
    is_revoked BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- USAGE TRACKING & KOSTEN
-- ===================================================

-- Nutzungsprotokolle
CREATE TABLE usage_logs (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,
    model_name VARCHAR(100) NOT NULL,
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    cost DECIMAL(10, 6) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- BEZAHLUNG & ABRECHNUNG
-- ===================================================

-- Zahlungen
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    stripe_payment_id VARCHAR(255) UNIQUE,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'completed', 'failed', 'refunded')),
    payment_method VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Rechnungen
CREATE TABLE invoices (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    invoice_number VARCHAR(50) UNIQUE NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    status VARCHAR(50) DEFAULT 'draft' CHECK (status IN ('draft', 'sent', 'paid', 'overdue', 'cancelled')),
    tax_amount DECIMAL(10, 2) DEFAULT 0.00,
    total_amount DECIMAL(10, 2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    due_date TIMESTAMP NOT NULL,
    paid_at TIMESTAMP
);

-- Benutzerguthaben
CREATE TABLE user_balance (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    balance DECIMAL(10, 2) DEFAULT 0.00,
    currency VARCHAR(3) DEFAULT 'USD',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ===================================================
-- INDIZES FÜR PERFORMANCE
-- ===================================================

-- Benutzer-Indizes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);

-- Projekt-Indizes
CREATE INDEX idx_projects_owner ON projects(owner_id);
CREATE INDEX idx_projects_is_shared ON projects(is_shared);

-- Ordner-Indizes
CREATE INDEX idx_folders_project ON folders(project_id);
CREATE INDEX idx_folders_parent ON folders(parent_folder_id);

-- Chat-Indizes
CREATE INDEX idx_chats_project ON chats(project_id);
CREATE INDEX idx_chats_folder ON chats(folder_id);
CREATE INDEX idx_chats_model ON chats(model_name);
CREATE INDEX idx_chats_archived ON chats(is_archived);

-- Nachrichten-Indizes
CREATE INDEX idx_messages_chat ON messages(chat_id);
CREATE INDEX idx_messages_role ON messages(role);
CREATE INDEX idx_messages_created_at ON messages(created_at);

-- API-Schlüssel-Indizes
CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_provider ON api_keys(provider);
CREATE INDEX idx_api_keys_is_active ON api_keys(is_active);

-- Token-Indizes
CREATE INDEX idx_tokens_user ON tokens(user_id);
CREATE INDEX idx_tokens_type ON tokens(token_type);
CREATE INDEX idx_tokens_expires_at ON tokens(expires_at);
CREATE INDEX idx_tokens_is_revoked ON tokens(is_revoked);

-- Nutzungs-Indizes
CREATE INDEX idx_usage_logs_user ON usage_logs(user_id);
CREATE INDEX idx_usage_logs_chat ON usage_logs(chat_id);
CREATE INDEX idx_usage_logs_provider ON usage_logs(provider);
CREATE INDEX idx_usage_logs_created_at ON usage_logs(created_at);

-- Zahlungs-Indizes
CREATE INDEX idx_payments_user ON payments(user_id);
CREATE INDEX idx_payments_status ON payments(status);
CREATE INDEX idx_payments_created_at ON payments(created_at);

-- Rechnungs-Indizes
CREATE INDEX idx_invoices_user ON invoices(user_id);
CREATE INDEX idx_invoices_status ON invoices(status);
CREATE INDEX idx_invoices_due_date ON invoices(due_date);

-- ===================================================
-- TRIGGER FÜR AUTOMATISCHE UPDATES
-- ===================================================

-- Function für updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger für alle Tabellen mit updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_folders_updated_at BEFORE UPDATE ON folders
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_chats_updated_at BEFORE UPDATE ON chats
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_payments_updated_at BEFORE UPDATE ON payments
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_balance_updated_at BEFORE UPDATE ON user_balance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===================================================
-- STANDARD-ROLLEN & BERECHTIGUNGEN
-- ===================================================

-- Basis-Rollen erstellen
INSERT INTO roles (name, description) VALUES
    ('user', 'Standard-Benutzer mit Basis-Berechtigungen'),
    ('admin', 'Administrator mit vollständigen Berechtigungen'),
    ('premium', 'Premium-Benutzer mit erweiterten Berechtigungen')
ON CONFLICT (name) DO NOTHING;

-- Basis-Berechtigungen erstellen
INSERT INTO permissions (name, resource, action, description) VALUES
    ('create_project', 'projects', 'create', 'Projekte erstellen'),
    ('edit_project', 'projects', 'update', 'Projekte bearbeiten'),
    ('delete_project', 'projects', 'delete', 'Projekte löschen'),
    ('view_project', 'projects', 'read', 'Projekte anzeigen'),
    ('create_chat', 'chats', 'create', 'Chats erstellen'),
    ('edit_chat', 'chats', 'update', 'Chats bearbeiten'),
    ('delete_chat', 'chats', 'delete', 'Chats löschen'),
    ('view_chat', 'chats', 'read', 'Chats anzeigen'),
    ('manage_api_keys', 'api_keys', 'manage', 'API-Schlüssel verwalten'),
    ('view_usage_logs', 'usage_logs', 'read', 'Nutzungsprotokolle anzeigen'),
    ('manage_payments', 'payments', 'manage', 'Zahlungen verwalten'),
    ('view_invoices', 'invoices', 'read', 'Rechnungen anzeigen'),
    ('admin_users', 'users', 'admin', 'Benutzer administrieren'),
    ('admin_system', 'system', 'admin', 'System administrieren')
ON CONFLICT (name) DO NOTHING;

-- Berechtigungen den Rollen zuweisen
INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM roles r, permissions p 
WHERE r.name = 'user' AND p.name IN (
    'create_project', 'edit_project', 'delete_project', 'view_project',
    'create_chat', 'edit_chat', 'delete_chat', 'view_chat',
    'manage_api_keys', 'view_usage_logs', 'view_invoices'
) ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM roles r, permissions p 
WHERE r.name = 'premium' AND p.name IN (
    'create_project', 'edit_project', 'delete_project', 'view_project',
    'create_chat', 'edit_chat', 'delete_chat', 'view_chat',
    'manage_api_keys', 'view_usage_logs', 'manage_payments', 'view_invoices'
) ON CONFLICT DO NOTHING;

INSERT INTO role_permissions (role_id, permission_id) 
SELECT r.id, p.id 
FROM roles r, permissions p 
WHERE r.name = 'admin'
ON CONFLICT DO NOTHING;

-- ===================================================
-- ENTWICKLUNGS-TESTDATEN
-- ===================================================

-- Test-Benutzer erstellen
INSERT INTO users (email, username, password_hash, full_name, is_admin, email_verified) VALUES
    ('admin@localhost', 'admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeUcpNYyZa4oEqrqG', 'Administrator', TRUE, TRUE),
    ('user@localhost', 'user', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeUcpNYyZa4oEqrqG', 'Test User', FALSE, TRUE),
    ('premium@localhost', 'premium', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LeUcpNYyZa4oEqrqG', 'Premium User', FALSE, TRUE)
ON CONFLICT (email) DO NOTHING;

-- Rollen zuweisen
INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'admin' AND r.name = 'admin'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'user' AND r.name = 'user'
ON CONFLICT DO NOTHING;

INSERT INTO user_roles (user_id, role_id) 
SELECT u.id, r.id 
FROM users u, roles r 
WHERE u.username = 'premium' AND r.name = 'premium'
ON CONFLICT DO NOTHING;

-- Benutzer-Guthaben initialisieren
INSERT INTO user_balance (user_id, balance) 
SELECT id, 10.00 FROM users
ON CONFLICT DO NOTHING;

-- Test-Projekt erstellen
INSERT INTO projects (name, description, owner_id, color) VALUES
    ('Beispiel-Projekt', 'Ein Beispiel-Projekt für die Entwicklung', 1, '#3B82F6'),
    ('Test-Projekt', 'Ein Test-Projekt für Demonstrationszwecke', 2, '#EF4444')
ON CONFLICT DO NOTHING;

-- Test-Ordner erstellen
INSERT INTO folders (name, description, project_id, color) VALUES
    ('Allgemeine Chats', 'Ordner für allgemeine Unterhaltungen', 1, '#6B7280'),
    ('Entwicklung', 'Ordner für Entwicklungsthemen', 1, '#10B981'),
    ('Dokumentation', 'Ordner für Dokumentation', 2, '#F59E0B')
ON CONFLICT DO NOTHING;

-- Test-Chat erstellen
INSERT INTO chats (title, project_id, folder_id, model_name, system_prompt) VALUES
    ('Willkommen Chat', 1, 1, 'gpt-4', 'Du bist ein hilfreicher Assistent für das LLM-Frontend.'),
    ('Entwicklungs-Chat', 1, 2, 'gpt-3.5-turbo', 'Du hilfst bei der Entwicklung des LLM-Frontends.')
ON CONFLICT DO NOTHING;

-- Test-Nachrichten erstellen
INSERT INTO messages (chat_id, role, content, token_count) VALUES
    (1, 'user', 'Hallo! Wie funktioniert dieses Frontend?', 150),
    (1, 'assistant', 'Willkommen beim LLM-Frontend! Dieses System ermöglicht es dir, mit verschiedenen Large Language Models zu interagieren...', 500),
    (2, 'user', 'Wie kann ich einen neuen Chat erstellen?', 100),
    (2, 'assistant', 'Um einen neuen Chat zu erstellen, klicke auf den "Neuer Chat" Button in der Sidebar...', 300)
ON CONFLICT DO NOTHING;

-- ===================================================
-- VIEWS FÜR HÄUFIGE ABFRAGEN
-- ===================================================

-- View für Benutzer mit Rollen
CREATE OR REPLACE VIEW user_roles_view AS
SELECT 
    u.id,
    u.email,
    u.username,
    u.full_name,
    u.is_active,
    u.is_admin,
    COALESCE(array_agg(r.name) FILTER (WHERE r.name IS NOT NULL), '{}') as roles
FROM users u
LEFT JOIN user_roles ur ON u.id = ur.user_id
LEFT JOIN roles r ON ur.role_id = r.id
GROUP BY u.id, u.email, u.username, u.full_name, u.is_active, u.is_admin;

-- View für Projekt-Statistiken
CREATE OR REPLACE VIEW project_stats_view AS
SELECT 
    p.id,
    p.name,
    p.description,
    p.owner_id,
    COUNT(DISTINCT c.id) as chat_count,
    COUNT(DISTINCT f.id) as folder_count,
    SUM(CASE WHEN c.is_archived = false THEN 1 ELSE 0 END) as active_chats,
    p.created_at,
    p.updated_at
FROM projects p
LEFT JOIN chats c ON p.id = c.project_id
LEFT JOIN folders f ON p.id = f.project_id
GROUP BY p.id, p.name, p.description, p.owner_id, p.created_at, p.updated_at;

-- View für Nutzungsstatistiken
CREATE OR REPLACE VIEW usage_stats_view AS
SELECT 
    u.id as user_id,
    u.username,
    COUNT(ul.id) as total_requests,
    SUM(ul.input_tokens) as total_input_tokens,
    SUM(ul.output_tokens) as total_output_tokens,
    SUM(ul.cost) as total_cost,
    DATE_TRUNC('month', ul.created_at) as month
FROM users u
LEFT JOIN usage_logs ul ON u.id = ul.user_id
WHERE ul.created_at >= CURRENT_DATE - INTERVAL '12 months'
GROUP BY u.id, u.username, DATE_TRUNC('month', ul.created_at);

-- ===================================================
-- FUNKTIONEN FÜR BUSINESS LOGIC
-- ===================================================

-- Funktion zum Aktualisieren des Benutzerguthabens
CREATE OR REPLACE FUNCTION update_user_balance(p_user_id INTEGER, p_amount DECIMAL)
RETURNS VOID AS $$
BEGIN
    INSERT INTO user_balance (user_id, balance) 
    VALUES (p_user_id, p_amount)
    ON CONFLICT (user_id) 
    DO UPDATE SET balance = user_balance.balance + p_amount, updated_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Funktion zum Protokollieren der Nutzung
CREATE OR REPLACE FUNCTION log_usage(
    p_user_id INTEGER,
    p_chat_id INTEGER,
    p_provider VARCHAR(50),
    p_model_name VARCHAR(100),
    p_input_tokens INTEGER,
    p_output_tokens INTEGER,
    p_cost DECIMAL
)
RETURNS VOID AS $$
BEGIN
    INSERT INTO usage_logs (user_id, chat_id, provider, model_name, input_tokens, output_tokens, cost)
    VALUES (p_user_id, p_chat_id, p_provider, p_model_name, p_input_tokens, p_output_tokens, p_cost);
    
    -- Guthaben reduzieren
    PERFORM update_user_balance(p_user_id, -p_cost);
END;
$$ LANGUAGE plpgsql;

-- ===================================================
-- DATENSCHUTZ & SICHERHEIT
-- ===================================================

-- Row Level Security (RLS) aktivieren
ALTER TABLE projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE folders ENABLE ROW LEVEL SECURITY;
ALTER TABLE chats ENABLE ROW LEVEL SECURITY;
ALTER TABLE messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE api_keys ENABLE ROW LEVEL SECURITY;
ALTER TABLE usage_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE invoices ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_balance ENABLE ROW LEVEL SECURITY;

-- Policies für Datensicherheit (werden in der Anwendung konfiguriert)
-- Beispiel: Benutzer können nur ihre eigenen Projekte sehen
CREATE POLICY projects_owner_policy ON projects
    FOR ALL USING (owner_id = current_setting('app.current_user_id')::INTEGER);

-- ===================================================
-- ABSCHLUSS
-- ===================================================

-- Analyse-Statistiken aktualisieren
ANALYZE;

-- Erfolgsmeldung
SELECT 'LLM-Frontend Schema erfolgreich erstellt!' as status; 