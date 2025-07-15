# scripts/validate_config.sh
#!/bin/bash
# Валидация конфигурации TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔍 Validating TopFlight Configuration..."

ERRORS=0
WARNINGS=0

# Функции для проверок
check_error() {
    echo "❌ $1"
    ((ERRORS++))
}

check_warning() {
    echo "⚠️ $1"
    ((WARNINGS++))
}

check_ok() {
    echo "✅ $1"
}

# Проверка структуры проекта
echo ""
echo "📁 PROJECT STRUCTURE"
if [ -d "$PROJECT_ROOT" ]; then
    check_ok "Project root exists: $PROJECT_ROOT"
else
    check_error "Project root not found: $PROJECT_ROOT"
fi

if [ -d "$BACKEND_DIR" ]; then
    check_ok "Backend directory exists"
else
    check_error "Backend directory not found"
fi

if [ -d "$PROJECT_ROOT/frontend" ]; then
    check_ok "Frontend directory exists"
else
    check_warning "Frontend directory not found"
fi

# Проверка Python окружения
echo ""
echo "🐍 PYTHON ENVIRONMENT"
if [ -f "$BACKEND_DIR/venv/bin/python" ]; then
    check_ok "Virtual environment exists"
    PYTHON_VERSION=$("$BACKEND_DIR/venv/bin/python" --version 2>&1)
    check_ok "Python version: $PYTHON_VERSION"
else
    check_error "Virtual environment not found"
fi

if [ -f "$BACKEND_DIR/requirements.txt" ]; then
    check_ok "Requirements file exists"
else
    check_error "Requirements file not found"
fi

# Проверка конфигурации
echo ""
echo "⚙️ CONFIGURATION"
if [ -f "$BACKEND_DIR/.env" ]; then
    check_ok ".env file exists"

    # Проверяем ключевые переменные
    source "$BACKEND_DIR/.env" 2>/dev/null || true

    if [ -n "${DATABASE_URL:-}" ]; then
        check_ok "DATABASE_URL configured"
    else
        check_error "DATABASE_URL not set"
    fi

    if [ -n "${SECRET_KEY:-}" ]; then
        check_ok "SECRET_KEY configured"
    else
        check_error "SECRET_KEY not set"
    fi

    if [ -n "${REDIS_URL:-}" ]; then
        check_ok "REDIS_URL configured"
    else
        check_warning "REDIS_URL not set"
    fi

else
    check_error ".env file not found"
fi

# Проверка системных сервисов
echo ""
echo "🔧 SYSTEM SERVICES"
if systemctl is-active --quiet xvfb-main 2>/dev/null; then
    check_ok "Xvfb main service running"
elif systemctl is-active --quiet xvfb 2>/dev/null; then
    check_ok "Xvfb service running"
else
    check_error "Xvfb service not running"
fi

if systemctl is-active --quiet postgresql 2>/dev/null; then
    check_ok "PostgreSQL service running"
else
    check_error "PostgreSQL service not running"
fi

if systemctl is-active --quiet redis-server 2>/dev/null || systemctl is-active --quiet redis 2>/dev/null; then
    check_ok "Redis service running"
else
    check_warning "Redis service not running"
fi

# Проверка портов
echo ""
echo "🔌 NETWORK PORTS"
if netstat -tlnp 2>/dev/null | grep -q ":8000 "; then
    check_ok "API port 8000 is listening"
else
    check_warning "API port 8000 not listening"
fi

if netstat -tlnp 2>/dev/null | grep -q ":5432 "; then
    check_ok "PostgreSQL port 5432 is listening"
else
    check_error "PostgreSQL port 5432 not listening"
fi

if netstat -tlnp 2>/dev/null | grep -q ":6379 "; then
    check_ok "Redis port 6379 is listening"
else
    check_warning "Redis port 6379 not listening"
fi

# Проверка прав доступа
echo ""
echo "🔐 PERMISSIONS"
if [ -r "$PROJECT_ROOT" ] && [ -w "$PROJECT_ROOT" ]; then
    check_ok "Project root permissions OK"
else
    check_error "Insufficient permissions on project root"
fi

if [ -f "$PROJECT_ROOT/logs" ] || mkdir -p "$PROJECT_ROOT/logs" 2>/dev/null; then
    check_ok "Logs directory writable"
else
    check_error "Cannot write to logs directory"
fi

# Проверка дисплея
echo ""
echo "🖥️ DISPLAY ENVIRONMENT"
export DISPLAY=:99
if xdpyinfo >/dev/null 2>&1; then
    check_ok "Display :99 accessible"
else
    check_error "Display :99 not accessible"
fi

# Сводка
echo ""
echo "📊 VALIDATION SUMMARY"
echo "=============================="
if [ $ERRORS -eq 0 ] && [ $WARNINGS -eq 0 ]; then
    echo "🎉 Configuration is perfect!"
elif [ $ERRORS -eq 0 ]; then
    echo "✅ Configuration is good (with $WARNINGS warnings)"
else
    echo "❌ Configuration has issues: $ERRORS errors, $WARNINGS warnings"
fi

echo ""
echo "Statistics:"
echo "  Errors: $ERRORS"
echo "  Warnings: $WARNINGS"

if [ $ERRORS -gt 0 ]; then
    echo ""
    echo "🔧 Fix errors before starting TopFlight"
    exit 1
fi

echo ""
echo "✅ Configuration validation completed"
