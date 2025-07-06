#!/bin/bash

# ===========================================
# Dependency Update Script für LLM-Frontend
# ===========================================

set -e

echo "🔄 Updating Dependencies for LLM-Frontend..."

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

# Virtual Environment prüfen/erstellen
setup_venv() {
    if [ ! -d ".venv" ]; then
        print_step "Creating virtual environment..."
        python3 -m venv .venv
    fi
    
    source .venv/bin/activate
    pip install --upgrade pip pip-tools
}

# Python Dependencies aktualisieren
update_python_deps() {
    print_step "Updating Python dependencies..."
    
    source .venv/bin/activate
    
    # Services mit requirements.txt
    PYTHON_SERVICES=("backend-core" "auth-service" "payment-service" "llm-proxy" "rag-service")
    
    for service in "${PYTHON_SERVICES[@]}"; do
        if [ -d "$service" ]; then
            print_step "Updating $service dependencies..."
            cd "$service"
            
            # Erstelle requirements.in falls nicht vorhanden
            if [ ! -f "requirements.in" ]; then
                print_warning "Creating requirements.in for $service..."
                # Konvertiere requirements.txt zu requirements.in
                if [ -f "requirements.txt" ]; then
                    # Entferne Version-Pins für requirements.in
                    sed 's/==.*$//' requirements.txt > requirements.in
                    sed 's/>=.*$//' requirements.in -i
                    sed 's/~=.*$//' requirements.in -i
                fi
            fi
            
            # Aktualisiere requirements.txt mit pip-tools
            if [ -f "requirements.in" ]; then
                pip-compile --upgrade --resolver=backtracking requirements.in
                print_step "$service dependencies updated!"
            else
                print_warning "No requirements.in found for $service"
            fi
            
            cd ..
        fi
    done
    
    # Development Dependencies
    if [ -f "requirements-dev.txt" ]; then
        print_step "Updating development dependencies..."
        pip install -r requirements-dev.txt
    fi
}

# Node.js Dependencies aktualisieren
update_node_deps() {
    print_step "Updating Node.js dependencies..."
    
    # Root package.json
    if [ -f "package.json" ]; then
        print_step "Updating root dependencies..."
        npm update
        npm audit fix || true
    fi
    
    # Node.js Services
    NODE_SERVICES=("frontend" "frontend-vite" "api-gateway")
    
    for service in "${NODE_SERVICES[@]}"; do
        if [ -d "$service" ] && [ -f "$service/package.json" ]; then
            print_step "Updating $service dependencies..."
            cd "$service"
            
            # Update dependencies
            npm update
            npm audit fix || true
            
            cd ..
        fi
    done
}

# Docker Base Images prüfen
check_docker_images() {
    print_step "Checking Docker base images..."
    
    # Suche nach Dockerfile-Dateien
    find . -name "Dockerfile" -not -path "./.git/*" | while read dockerfile; do
        echo "📋 Checking $dockerfile:"
        
        # Extrahiere FROM-Zeilen
        grep "FROM" "$dockerfile" | while read line; do
            echo "  $line"
        done
        echo ""
    done
    
    print_warning "Please manually check if Docker base images need updates"
}

# Security Audit
security_audit() {
    print_step "Running security audit..."
    
    source .venv/bin/activate
    
    # Python Security Check
    if command -v safety &> /dev/null; then
        print_step "Running Python safety check..."
        safety check || print_warning "Safety check found issues"
    fi
    
    # Node.js Security Check
    if [ -f "package.json" ]; then
        print_step "Running Node.js audit..."
        npm audit --audit-level=moderate || print_warning "NPM audit found issues"
    fi
    
    # Secrets Check
    if command -v detect-secrets &> /dev/null; then
        print_step "Running secrets detection..."
        detect-secrets scan --baseline .secrets.baseline || print_warning "Secrets check found issues"
    fi
}

# Requirements-Dateien validieren
validate_requirements() {
    print_step "Validating requirements files..."
    
    source .venv/bin/activate
    
    PYTHON_SERVICES=("backend-core" "auth-service" "payment-service" "llm-proxy" "rag-service")
    
    for service in "${PYTHON_SERVICES[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            print_step "Validating $service/requirements.txt..."
            
            # Versuche Installation in temporärer Umgebung
            python -m venv "temp_venv_$service"
            source "temp_venv_$service/bin/activate"
            
            if pip install -r "$service/requirements.txt" > /dev/null 2>&1; then
                print_step "$service requirements are valid"
            else
                print_error "$service requirements have conflicts!"
            fi
            
            deactivate
            rm -rf "temp_venv_$service"
        fi
    done
}

# Bericht erstellen
create_report() {
    print_step "Creating dependency report..."
    
    cat > DEPENDENCY_REPORT.md << EOF
# Dependency Update Report

Generated on: $(date)

## Python Dependencies

### Services
EOF

    # Python Services
    PYTHON_SERVICES=("backend-core" "auth-service" "payment-service" "llm-proxy" "rag-service")
    
    for service in "${PYTHON_SERVICES[@]}"; do
        if [ -f "$service/requirements.txt" ]; then
            echo "#### $service" >> DEPENDENCY_REPORT.md
            echo '```' >> DEPENDENCY_REPORT.md
            head -20 "$service/requirements.txt" >> DEPENDENCY_REPORT.md
            echo '```' >> DEPENDENCY_REPORT.md
            echo "" >> DEPENDENCY_REPORT.md
        fi
    done
    
    cat >> DEPENDENCY_REPORT.md << EOF

## Node.js Dependencies

### Root Package
EOF
    
    if [ -f "package.json" ]; then
        echo '```json' >> DEPENDENCY_REPORT.md
        jq '.dependencies // {}, .devDependencies // {}' package.json >> DEPENDENCY_REPORT.md
        echo '```' >> DEPENDENCY_REPORT.md
    fi
    
    print_step "Report created: DEPENDENCY_REPORT.md"
}

# Informationen anzeigen
show_info() {
    echo ""
    echo "🎉 Dependency update completed!"
    echo ""
    echo "📋 What was done:"
    echo "   ✓ Python dependencies updated with pip-tools"
    echo "   ✓ Node.js dependencies updated"
    echo "   ✓ Security audit performed"
    echo "   ✓ Requirements validation completed"
    echo "   ✓ Dependency report generated"
    echo ""
    echo "📝 Next steps:"
    echo "   1. Review DEPENDENCY_REPORT.md"
    echo "   2. Test the application: npm run dev"
    echo "   3. Run tests: npm run test"
    echo "   4. Commit changes: git add . && git commit -m 'deps: update dependencies'"
    echo ""
    echo "🔧 Manual checks needed:"
    echo "   - Docker base image updates"
    echo "   - Breaking changes in major version updates"
    echo "   - Security advisories"
}

# Hauptprogramm
main() {
    setup_venv
    update_python_deps
    update_node_deps
    check_docker_images
    security_audit
    validate_requirements
    create_report
    show_info
}

# Script ausführen
main "$@" 