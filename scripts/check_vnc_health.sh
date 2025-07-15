#!/bin/bash

# Скрипт проверки здоровья VNC сессий
# /app/scripts/check_vnc_health.sh

set -euo pipefail

LOG_FILE="/app/logs/vnc_health.log"
HEALTH_ENDPOINT="http://localhost:8000/admin/debug/sessions"

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

check_vnc_sessions() {
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

            task_id=$(echo "$session" | jq -r '.task_id')
            vnc_port=$(echo "$session" | jq -r '.vnc_port')
            status=$(echo "$session" | jq -r '.status')

            if [ "$status" != "active" ]; then
                log_message "WARNING: Session $task_id is in $status state"
            fi

            # Проверяем доступность VNC порта
            if ! nc -z localhost "$vnc_port" 2>/dev/null; then
                log_message "ERROR: VNC port $vnc_port for task $task_id is not accessible"
            fi
        done
    fi
}

# Основной цикл мониторинга
while true; do
    check_vnc_sessions
    sleep 300  # Проверка каждые 5 минут
done
