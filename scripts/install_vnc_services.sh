#!/bin/bash

# Установка и настройка VNC сервисов для TopFlight
# scripts/install_vnc_services.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
LOGS_DIR="$PROJECT_ROOT/logs"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

echo "🚀 Installing TopFlight VNC services..."

# Проверяем, что мы в правильной директории
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Project directory $PROJECT_ROOT not found!"
    exit 1
fi

# Создаем необходимые директории
echo "📁 Creating directories..."
sudo mkdir -p "$LOGS_DIR"
sudo mkdir -p "$PROJECT_ROOT/data/vnc"
sudo mkdir -p "$PROJECT_ROOT/data/vnc_tokens"
sudo mkdir -p "/tmp/vnc_displays"

# Устанавливаем права
sudo chown -R oleg:oleg "$PROJECT_ROOT/data"
sudo chown -R oleg:oleg "$LOGS_DIR"
sudo chmod 755 "$LOGS_DIR"

# Создаем systemd сервис для основного Xvfb
echo "🔧 Creating xvfb-main.service..."
sudo tee /etc/systemd/system/xvfb-main.service > /dev/null <<EOF
[Unit]
Description=Xvfb Main Display for TopFlight Browser Profiles
After=network.target
Wants=network.target

[Service]
Type=simple
User=topflight
Group=topflight
Environment=DISPLAY=:99
Environment=PROJECT_ROOT=$PROJECT_ROOT
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp +extension GLX +extension RANDR -dpi 96
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ресурсы и лимиты
MemoryLimit=512M
CPUQuota=20%

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_ROOT $LOGS_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

# Создаем systemd сервис для VNC cleanup
echo "🔧 Creating vnc-cleanup.service..."
sudo tee /etc/systemd/system/vnc-cleanup.service > /dev/null <<EOF
[Unit]
Description=TopFlight VNC Sessions Cleanup Service
After=network.target postgresql.service redis.service
Wants=network.target

[Service]
Type=simple
User=topflight
Group=topflight
WorkingDirectory=$PROJECT_ROOT/backend
Environment=PYTHONPATH=$PROJECT_ROOT/backend
Environment=PROJECT_ROOT=$PROJECT_ROOT
ExecStart=$PROJECT_ROOT/backend/venv/bin/python -m app.core.vnc_cleanup_daemon
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

# Ресурсы
MemoryLimit=256M
CPUQuota=10%

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_ROOT $LOGS_DIR /tmp

[Install]
WantedBy=multi-user.target
EOF

# Создаем systemd сервис для VNC health monitor
echo "🔧 Creating vnc-health-monitor.service..."
sudo tee /etc/systemd/system/vnc-health-monitor.service > /dev/null <<EOF
[Unit]
Description=TopFlight VNC Health Monitor
After=network.target
Wants=network.target

[Service]
Type=simple
User=topflight
Group=topflight
WorkingDirectory=$PROJECT_ROOT
Environment=PROJECT_ROOT=$PROJECT_ROOT
ExecStart=$SCRIPTS_DIR/vnc_health_monitor.sh
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Создаем скрипты управления
echo "📝 Creating management scripts..."

# Скрипт запуска debug сессии
cat > "$SCRIPTS_DIR/start_debug_session.sh" << 'EOF'
#!/bin/bash
# Скрипт запуска debug сессии для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
TASK_ID=${1:-}
DEVICE_TYPE=${2:-desktop}
LOG_FILE="$PROJECT_ROOT/logs/vnc_debug.log"
ADMIN_TOKEN=${ADMIN_TOKEN:-}

if [ -z "$TASK_ID" ]; then
    echo "Usage: $0 TASK_ID [DEVICE_TYPE]"
    echo "Example: $0 uuid-here desktop"
    exit 1
fi

if [ -z "$ADMIN_TOKEN" ]; then
    echo "ERROR: ADMIN_TOKEN environment variable not set"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') Starting debug session for task $TASK_ID (device: $DEVICE_TYPE)" >> "$LOG_FILE"

# Проверяем доступность API
if ! curl -f -s "http://localhost:8000/health" > /dev/null; then
    echo "ERROR: TopFlight API server is not available" >> "$LOG_FILE"
    exit 1
fi

# Запускаем debug сессию через API
RESPONSE=$(curl -s -X POST \
    "http://localhost:8000/admin/debug/start/$TASK_ID?device_type=$DEVICE_TYPE" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json")

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    VNC_PORT=$(echo "$RESPONSE" | jq -r '.debug_info.vnc_port // empty')
    WEB_VNC_URL=$(echo "$RESPONSE" | jq -r '.debug_info.web_vnc_url // empty')

    echo "$(date '+%Y-%m-%d %H:%M:%S') Debug session started successfully" >> "$LOG_FILE"
    echo "✅ Debug session started for task: $TASK_ID"

    if [ -n "$VNC_PORT" ]; then
        echo "🖥️  VNC connection: vncviewer localhost:$VNC_PORT"
    fi

    if [ -n "$WEB_VNC_URL" ]; then
        echo "🌐 Web VNC: $WEB_VNC_URL"
    fi

    exit 0
else
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.detail // "Unknown error"')
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to start debug session: $ERROR_MSG" >> "$LOG_FILE"
    echo "❌ Failed to start debug session: $ERROR_MSG"
    exit 1
fi
EOF

# Скрипт остановки debug сессии
cat > "$SCRIPTS_DIR/stop_debug_session.sh" << 'EOF'
#!/bin/bash
# Скрипт остановки debug сессии для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
TASK_ID=${1:-}
LOG_FILE="$PROJECT_ROOT/logs/vnc_debug.log"
ADMIN_TOKEN=${ADMIN_TOKEN:-}

if [ -z "$TASK_ID" ]; then
    echo "Usage: $0 TASK_ID"
    echo "Example: $0 uuid-here"
    exit 1
fi

if [ -z "$ADMIN_TOKEN" ]; then
    echo "ERROR: ADMIN_TOKEN environment variable not set"
    exit 1
fi

echo "$(date '+%Y-%m-%d %H:%M:%S') Stopping debug session for task $TASK_ID" >> "$LOG_FILE"

# Останавливаем debug сессию через API
RESPONSE=$(curl -s -X POST \
    "http://localhost:8000/admin/debug/stop/$TASK_ID" \
    -H "Authorization: Bearer $ADMIN_TOKEN" \
    -H "Content-Type: application/json")

if echo "$RESPONSE" | jq -e '.success' > /dev/null 2>&1; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') Debug session stopped successfully" >> "$LOG_FILE"
    echo "✅ Debug session stopped for task: $TASK_ID"
    exit 0
else
    ERROR_MSG=$(echo "$RESPONSE" | jq -r '.detail // "Unknown error"')
    echo "$(date '+%Y-%m-%d %H:%M:%S') ERROR: Failed to stop debug session: $ERROR_MSG" >> "$LOG_FILE"
    echo "❌ Failed to stop debug session: $ERROR_MSG"
    exit 1
fi
EOF

# Скрипт проверки здоровья VNC
cat > "$SCRIPTS_DIR/vnc_health_monitor.sh" << 'EOF'
#!/bin/bash
# Скрипт мониторинга здоровья VNC сессий для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
LOG_FILE="$PROJECT_ROOT/logs/vnc_health.log"
HEALTH_ENDPOINT="http://localhost:8000/admin/debug/sessions"
ADMIN_TOKEN=${ADMIN_TOKEN:-}

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

check_vnc_sessions() {
    if [ -z "$ADMIN_TOKEN" ]; then
        log_message "WARNING: ADMIN_TOKEN not set, skipping API checks"
        return
    fi

    local sessions_response
    sessions_response=$(curl -s "$HEALTH_ENDPOINT" -H "Authorization: Bearer $ADMIN_TOKEN" 2>/dev/null || echo '[]')

    local session_count
    session_count=$(echo "$sessions_response" | jq length 2>/dev/null || echo "0")

    log_message "Active VNC sessions: $session_count"

    # Проверяем каждую сессию
    if [ "$session_count" -gt 0 ]; then
        echo "$sessions_response" | jq -c '.[]' | while read -r session; do
            local task_id
            local vnc_port
            local status

            task_id=$(echo "$session" | jq -r '.task_id // "unknown"')
            vnc_port=$(echo "$session" | jq -r '.vnc_port // "0"')
            status=$(echo "$session" | jq -r '.status // "unknown"')

            if [ "$status" != "active" ]; then
                log_message "WARNING: Session $task_id is in $status state"
            fi

            # Проверяем доступность VNC порта
            if [ "$vnc_port" != "0" ] && ! nc -z localhost "$vnc_port" 2>/dev/null; then
                log_message "ERROR: VNC port $vnc_port for task $task_id is not accessible"
            fi
        done
    fi
}

check_system_resources() {
    # Проверка использования памяти
    local mem_usage
    mem_usage=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100.0}')
    log_message "Memory usage: ${mem_usage}%"

    # Проверка использования CPU
    local cpu_usage
    cpu_usage=$(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)
    log_message "CPU usage: ${cpu_usage}%"

    # Проверка дискового пространства
    local disk_usage
    disk_usage=$(df -h "$PROJECT_ROOT" | awk 'NR==2{print $5}' | cut -d'%' -f1)
    log_message "Disk usage: ${disk_usage}%"

    # Предупреждения
    if (( $(echo "$mem_usage > 85" | bc -l) )); then
        log_message "WARNING: High memory usage: ${mem_usage}%"
    fi

    if (( disk_usage > 85 )); then
        log_message "WARNING: High disk usage: ${disk_usage}%"
    fi
}

# Основной цикл мониторинга
main_loop() {
    log_message "Starting VNC health monitoring for TopFlight"

    while true; do
        check_vnc_sessions
        check_system_resources
        sleep 300  # Проверка каждые 5 минут
    done
}

# Обработка сигналов
cleanup() {
    log_message "VNC health monitor stopped"
    exit 0
}

trap cleanup SIGTERM SIGINT

# Запуск
main_loop
EOF

# Скрипт экстренной очистки
cat > "$SCRIPTS_DIR/vnc_emergency_cleanup.sh" << 'EOF'
#!/bin/bash
# Экстренная очистка всех VNC процессов для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
LOG_FILE="$PROJECT_ROOT/logs/vnc_emergency.log"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" | tee -a "$LOG_FILE"
}

log_message "🚨 Emergency VNC cleanup started..."

# Убиваем все процессы VNC
log_message "Killing all x11vnc processes..."
sudo pkill -f "x11vnc" || true

# Убиваем все Xvfb процессы (кроме :99 - основного)
log_message "Killing debug Xvfb processes..."
for display in {100..199}; do
    if pgrep -f "Xvfb :$display" > /dev/null; then
        log_message "Killing Xvfb :$display"
        sudo pkill -f "Xvfb :$display" || true
    fi
done

# Очищаем lock файлы
log_message "Cleaning display lock files..."
sudo rm -f /tmp/.X*-lock
sudo rm -f /tmp/.X11-unix/X{100..199}

# Очищаем VNC данные
log_message "Cleaning VNC data..."
rm -f "$PROJECT_ROOT/data/vnc_tokens/vnc_tokens.conf"
touch "$PROJECT_ROOT/data/vnc_tokens/vnc_tokens.conf"
chown oleg:oleg "$PROJECT_ROOT/data/vnc_tokens/vnc_tokens.conf"

# Очищаем VNC сессии через API если доступно
if curl -f -s "http://localhost:8000/health" > /dev/null 2>&1; then
    log_message "Cleaning VNC sessions via API..."
    if [ -n "${ADMIN_TOKEN:-}" ]; then
        curl -s -X POST "http://localhost:8000/admin/debug/cleanup" \
            -H "Authorization: Bearer $ADMIN_TOKEN" || true
    else
        log_message "WARNING: ADMIN_TOKEN not set, skipping API cleanup"
    fi
fi

log_message "✅ Emergency cleanup completed"
EOF

# Делаем скрипты исполняемыми
chmod +x "$SCRIPTS_DIR"/*.sh

# Устанавливаем права на скрипты
sudo chown oleg:oleg "$SCRIPTS_DIR"/*.sh

# Перезагружаем systemd
sudo systemctl daemon-reload

# Включаем и запускаем сервисы
echo "🔄 Enabling and starting services..."
sudo systemctl enable xvfb-main.service
sudo systemctl enable vnc-cleanup.service
sudo systemctl enable vnc-health-monitor.service

sudo systemctl start xvfb-main.service
sudo systemctl start vnc-cleanup.service
sudo systemctl start vnc-health-monitor.service

echo "✅ TopFlight VNC services installed and started successfully"

# Проверяем статус
echo "📊 Service Status:"
sudo systemctl status xvfb-main.service --no-pager || true
sudo systemctl status vnc-cleanup.service --no-pager || true
sudo systemctl status vnc-health-monitor.service --no-pager || true

echo ""
echo "🎯 Next steps:"
echo "1. Set ADMIN_TOKEN environment variable for VNC management"
echo "2. Test VNC system: $SCRIPTS_DIR/test_vnc_system.sh"
echo "3. Check logs: tail -f $LOGS_DIR/vnc_debug.log"
