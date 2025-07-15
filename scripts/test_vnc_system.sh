#!/bin/bash

# Тестирование VNC системы TopFlight
# scripts/test_vnc_system.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
TEST_LOG="$PROJECT_ROOT/logs/vnc_test.log"

echo "🧪 Testing TopFlight VNC System..."

# Функция логирования
log_test() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') TEST: $1" | tee -a "$TEST_LOG"
}

# Тест 1: Проверка Xvfb
log_test "Checking Xvfb service..."
if sudo systemctl is-active --quiet xvfb-main; then
    log_test "✅ Xvfb service is running"
else
    log_test "❌ Xvfb service is not running"
    exit 1
fi

# Тест 2: Проверка DISPLAY
log_test "Testing DISPLAY environment..."
export DISPLAY=:99
if xdpyinfo >/dev/null 2>&1; then
    log_test "✅ DISPLAY :99 is accessible"
else
    log_test "❌ DISPLAY :99 is not accessible"
    exit 1
fi

# Тест 3: Проверка API
log_test "Testing API health..."
if curl -f -s "http://localhost:8000/health" >/dev/null; then
    log_test "✅ API is responding"
else
    log_test "❌ API is not responding"
    exit 1
fi

# Тест 4: Проверка портов VNC
log_test "Checking VNC port range..."
VNC_PORTS_AVAILABLE=0
for port in {5900..5910}; do
    if ! nc -z localhost "$port" 2>/dev/null; then
        ((VNC_PORTS_AVAILABLE++))
    fi
done

if [ $VNC_PORTS_AVAILABLE -gt 5 ]; then
    log_test "✅ VNC ports available: $VNC_PORTS_AVAILABLE"
else
    log_test "⚠️ Limited VNC ports available: $VNC_PORTS_AVAILABLE"
fi

# Тест 5: Проверка директорий
log_test "Checking directories..."
REQUIRED_DIRS=(
    "$PROJECT_ROOT/logs"
    "$PROJECT_ROOT/data/vnc"
    "$PROJECT_ROOT/data/vnc_tokens"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ -d "$dir" ] && [ -w "$dir" ]; then
        log_test "✅ Directory accessible: $dir"
    else
        log_test "❌ Directory issue: $dir"
        exit 1
    fi
done

# Тест 6: Проверка прав
log_test "Checking permissions..."
if [ -x "$PROJECT_ROOT/scripts/start_debug_session.sh" ]; then
    log_test "✅ VNC scripts are executable"
else
    log_test "❌ VNC scripts are not executable"
    exit 1
fi

echo ""
log_test "🎉 All VNC system tests passed!"
echo "System is ready for VNC debugging."

