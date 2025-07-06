#!/bin/bash

# ===========================================
# Pre-commit Hooks Setup Script
# ===========================================

set -e

echo "🔧 Setting up Pre-commit Hooks for LLM-Frontend..."

# Farben für Output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Funktionen
print_step() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

# Überprüfung der Systemvoraussetzungen
check_requirements() {
    print_step "Checking system requirements..."
    
    # Python prüfen
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 ist nicht installiert."
        exit 1
    fi
    
    # Node.js prüfen
    if ! command -v node &> /dev/null; then
        print_error "Node.js ist nicht installiert."
        exit 1
    fi
    
    # NPM prüfen
    if ! command -v npm &> /dev/null; then
        print_error "NPM ist nicht installiert."
        exit 1
    fi
    
    print_step "All requirements satisfied!"
}

# Python Virtual Environment erstellen
setup_python_env() {
    print_step "Setting up Python virtual environment..."
    
    # Virtual Environment erstellen falls nicht vorhanden
    if [ ! -d ".venv" ]; then
        python3 -m venv .venv
        print_step "Created virtual environment"
    else
        print_warning "Virtual environment already exists"
    fi
    
    # Virtual Environment aktivieren
    source .venv/bin/activate
    
    # Pip upgraden
    pip install --upgrade pip
    
    # Pre-commit installieren
    pip install pre-commit
    
    # Python linting tools installieren
    pip install black isort flake8 bandit
    
    print_step "Python environment setup complete!"
}

# Node.js Dependencies installieren
setup_node_deps() {
    print_step "Setting up Node.js dependencies..."
    
    # Global ESLint und Prettier installieren
    npm install -g eslint prettier
    
    # Prüfen ob package.json existiert
    if [ ! -f "package.json" ]; then
        print_step "Creating package.json..."
        npm init -y
    fi
    
    # Dev Dependencies installieren
    npm install --save-dev \
        eslint \
        prettier \
        @typescript-eslint/eslint-plugin \
        @typescript-eslint/parser \
        eslint-config-prettier \
        eslint-plugin-prettier \
        eslint-plugin-react \
        eslint-plugin-react-hooks \
        eslint-plugin-jsx-a11y \
        eslint-plugin-import \
        typescript
    
    print_step "Node.js dependencies setup complete!"
}

# Pre-commit-Hooks installieren
install_precommit_hooks() {
    print_step "Installing pre-commit hooks..."
    
    # Virtual Environment aktivieren
    source .venv/bin/activate
    
    # Pre-commit-Hooks installieren
    pre-commit install
    
    # Pre-commit-Hooks für commit-msg installieren
    pre-commit install --hook-type commit-msg
    
    print_step "Pre-commit hooks installed!"
}

# Test-Lauf durchführen
test_precommit() {
    print_step "Running pre-commit test..."
    
    # Virtual Environment aktivieren
    source .venv/bin/activate
    
    # Alle Hooks auf alle Dateien anwenden
    pre-commit run --all-files || true
    
    print_step "Pre-commit test completed!"
}

# Secrets-Baseline erstellen
setup_secrets_baseline() {
    print_step "Setting up secrets baseline..."
    
    # Virtual Environment aktivieren
    source .venv/bin/activate
    
    # detect-secrets installieren
    pip install detect-secrets
    
    # Baseline erstellen
    detect-secrets scan --baseline .secrets.baseline
    
    print_step "Secrets baseline created!"
}

# Informationen anzeigen
show_info() {
    echo ""
    echo "🎉 Pre-commit hooks setup complete!"
    echo ""
    echo "📋 Available commands:"
    echo "   pre-commit run --all-files    # Run all hooks on all files"
    echo "   pre-commit run <hook-name>    # Run specific hook"
    echo "   pre-commit autoupdate         # Update hook versions"
    echo "   pre-commit uninstall          # Remove hooks"
    echo ""
    echo "🔧 Linting tools:"
    echo "   black --check .               # Check Python formatting"
    echo "   isort --check-only .          # Check import sorting"
    echo "   flake8 .                      # Python linting"
    echo "   bandit -r .                   # Security linting"
    echo "   eslint .                      # JavaScript linting"
    echo "   prettier --check .            # Check formatting"
    echo ""
    echo "📝 Configuration files:"
    echo "   .pre-commit-config.yaml       # Pre-commit configuration"
    echo "   .flake8                       # Python linting config"
    echo "   .eslintrc.js                  # JavaScript linting config"
    echo "   .prettierrc.js                # Code formatting config"
    echo ""
    echo "💡 Tips:"
    echo "   - Hooks run automatically on git commit"
    echo "   - Use 'git commit --no-verify' to skip hooks (not recommended)"
    echo "   - Run 'pre-commit run --all-files' before pushing"
}

# Hauptprogramm
main() {
    check_requirements
    setup_python_env
    setup_node_deps
    install_precommit_hooks
    setup_secrets_baseline
    test_precommit
    show_info
}

# Script ausführen
main "$@" 