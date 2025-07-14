#!/bin/bash
# Скрипт очистки VNC сессий
set -euo pipefail

LOG_FILE="/var/log/vnc-debug/cleanup.log"
mkdir -p "$(dirname "$LOG_FILE")"

echo "$(date) - VNC cleanup started" >> "$LOG_FILE"

# Очищаем старые PID файлы
for pid_file in /tmp/debug-*.pid; do
    [[ -f "$pid_file" ]] || continue
    PID=$(cat "$pid_file" 2>/dev/null || echo "")
    if [[ -n "$PID" ]] && ! kill -0 "$PID" 2>/dev/null; then
        rm -f "$pid_file"
        echo "$(date) - Removed stale PID file: $pid_file" >> "$LOG_FILE"
    fi
done

# Убиваем старые VNC процессы (>2 часов)
OLD_VNC_PIDS=$(ps -eo pid,etimes,cmd | awk '/x11vnc.*-rfbport/ && $2 > 7200 {print $1}' || true)
for pid in $OLD_VNC_PIDS; do
    [[ -n "$pid" ]] || continue
    echo "$(date) - Killing old VNC process: $pid" >> "$LOG_FILE"
    kill -9 "$pid" 2>/dev/null || true
done

# Убиваем старые Xvfb процессы в диапазоне debug дисплеев (>2 часов)
OLD_XVFB_PIDS=$(ps -eo pid,etimes,cmd | awk '/Xvfb.*:1[0-4][0-9]/ && $2 > 7200 {print $1}' || true)
for pid in $OLD_XVFB_PIDS; do
    [[ -n "$pid" ]] || continue
    echo "$(date) - Killing old Xvfb process: $pid" >> "$LOG_FILE"
    kill -9 "$pid" 2>/dev/null || true
done

# Очищаем старые лог файлы (старше 7 дней)
find "/var/log/vnc-debug/" -name "debug-session-*.log" -mtime +7 -delete 2>/dev/null || true

echo "$(date) - VNC cleanup completed" >> "$LOG_FILE"
