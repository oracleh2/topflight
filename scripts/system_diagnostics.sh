#!/bin/bash

# Диагностика системы TopFlight
# scripts/system_diagnostics.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
DIAG_LOG="$PROJECT_ROOT/logs/diagnostics_$(date +%Y%m%d_%H%M%S).log"

echo "🔍 TopFlight System Diagnostics" | tee "$DIAG_LOG"
echo "Generated: $(date)" | tee -a "$DIAG_LOG"
echo "======================================" | tee -a "$DIAG_LOG"

# Системная информация
echo -e "\n📊 SYSTEM INFORMATION" | tee -a "$DIAG_LOG"
{
    echo "Hostname: $(hostname)"
    echo "OS: $(lsb_release -d | cut -f2)"
    echo "Kernel: $(uname -r)"
    echo "Uptime: $(uptime)"
    echo "Users: $(who | wc -l) logged in"
} | tee -a "$DIAG_LOG"

# Ресурсы системы
echo -e "\n💾 SYSTEM RESOURCES" | tee -a "$DIAG_LOG"
{
    echo "CPU Info:"
    lscpu | grep "Model name\|CPU(s)\|MHz"
    echo -e "\nMemory Info:"
    free -h
    echo -e "\nDisk Space:"
    df -h "$PROJECT_ROOT"
    echo -e "\nLoad Average:"
    cat /proc/loadavg
} | tee -a "$DIAG_LOG"

# Сетевые интерфейсы
echo -e "\n🌐 NETWORK INTERFACES" | tee -a "$DIAG_LOG"
ip addr show | grep -E "^\d+:|inet " | tee -a "$DIAG_LOG"

# Сервисы TopFlight
echo -e "\n⚙️ TOPFLIGHT SERVICES" | tee -a "$DIAG_LOG"
SERVICES=(
    "xvfb-main"
    "vnc-cleanup"
    "vnc-health-monitor"
    "postgresql"
    "redis-server"
    "nginx"
)

for service in "${SERVICES[@]}"; do
    if systemctl is-active --quiet "$service" 2>/dev/null; then
        echo "✅ $service: RUNNING" | tee -a "$DIAG_LOG"
    else
        echo "❌ $service: STOPPED" | tee -a "$DIAG_LOG"
    fi
done

# Процессы TopFlight
echo -e "\n🔄 TOPFLIGHT PROCESSES" | tee -a "$DIAG_LOG"
{
    echo "Python processes:"
    pgrep -fl "python.*topflight\|python.*run_api\|python.*run_worker" || echo "No Python processes found"
    echo -e "\nXvfb processes:"
    pgrep -fl "Xvfb" || echo "No Xvfb processes found"
    echo -e "\nVNC processes:"
    pgrep -fl "x11vnc" || echo "No VNC processes found"
} | tee -a "$DIAG_LOG"

# Порты
echo -e "\n🔌 LISTENING PORTS" | tee -a "$DIAG_LOG"
{
    echo "TopFlight related ports:"
    netstat -tlnp 2>/dev/null | grep -E ":8000\s|:5432\s|:6379\s|:590[0-9]\s|:6080\s" || echo "No TopFlight ports found"
} | tee -a "$DIAG_LOG"

# Логи ошибок
echo -e "\n📋 RECENT ERROR LOGS" | tee -a "$DIAG_LOG"
{
    echo "System journal errors (last 10):"
    journalctl --no-pager -p err -n 10 --since "1 hour ago" | tail -10

    echo -e "\nTopFlight application errors:"
    if [ -f "$PROJECT_ROOT/logs/backend.log" ]; then
        tail -20 "$PROJECT_ROOT/logs/backend.log" | grep -i error || echo "No recent errors in backend.log"
    else
        echo "Backend log not found"
    fi
} | tee -a "$DIAG_LOG"

# Конфигурация
echo -e "\n⚙️ CONFIGURATION CHECK" | tee -a "$DIAG_LOG"
{
    echo "Project root permissions:"
    ls -la "$PROJECT_ROOT" | head -5

    echo -e "\nEnvironment variables:"
    env | grep -E "DISPLAY|PROJECT_ROOT|DATABASE_URL" || echo "No relevant env vars found"

    echo -e "\nPython virtual environment:"
    if [ -f "$PROJECT_ROOT/backend/venv/bin/python" ]; then
        echo "✅ Virtual environment exists"
        "$PROJECT_ROOT/backend/venv/bin/python" --version
    else
        echo "❌ Virtual environment not found"
    fi
} | tee -a "$DIAG_LOG"

# База данных
echo -e "\n🗄️ DATABASE STATUS" | tee -a "$DIAG_LOG"
{
    echo "PostgreSQL connection test:"
    if command -v psql >/dev/null 2>&1; then
        if psql -h localhost -U postgres -d yandex_parser -c "SELECT version();" >/dev/null 2>&1; then
            echo "✅ Database connection successful"
            psql -h localhost -U postgres -d yandex_parser -c "SELECT COUNT(*) as total_tables FROM information_schema.tables WHERE table_schema = 'public';" 2>/dev/null || echo "Could not count tables"
        else
            echo "❌ Database connection failed"
        fi
    else
        echo "⚠️ psql command not available"
    fi
} | tee -a "$DIAG_LOG"

# Redis
echo -e "\n🔄 REDIS STATUS" | tee -a "$DIAG_LOG"
{
    echo "Redis connection test:"
    if command -v redis-cli >/dev/null 2>&1; then
        if redis-cli ping >/dev/null 2>&1; then
            echo "✅ Redis connection successful"
            echo "Redis info: $(redis-cli info server | grep redis_version)"
        else
            echo "❌ Redis connection failed"
        fi
    else
        echo "⚠️ redis-cli command not available"
    fi
} | tee -a "$DIAG_LOG"

# Рекомендации
echo -e "\n💡 RECOMMENDATIONS" | tee -a "$DIAG_LOG"
{
    # Проверка места на диске
    DISK_USAGE=$(df "$PROJECT_ROOT" | awk 'NR==2{print $5}' | cut -d'%' -f1)
    if [ "$DISK_USAGE" -gt 80 ]; then
        echo "⚠️ Disk usage is high ($DISK_USAGE%). Consider cleaning up logs or expanding storage."
    fi

    # Проверка памяти
    MEM_USAGE=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100.0}')
    if [ "$MEM_USAGE" -gt 85 ]; then
        echo "⚠️ Memory usage is high ($MEM_USAGE%). Consider adding more RAM or optimizing processes."
    fi

    # Проверка логов
    if [ -f "$PROJECT_ROOT/logs/vnc_debug.log" ]; then
        LOG_SIZE=$(du -sh "$PROJECT_ROOT/logs/vnc_debug.log" | cut -f1)
        echo "📋 VNC debug log size: $LOG_SIZE"
    fi

    echo "✅ Diagnostics completed. Check log file: $DIAG_LOG"
} | tee -a "$DIAG_LOG"

echo -e "\n======================================" | tee -a "$DIAG_LOG"
echo "Diagnostics saved to: $DIAG_LOG"
