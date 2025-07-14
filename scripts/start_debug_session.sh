#!/bin/bash
set -euo pipefail

TASK_ID="${1:-}"
DEVICE_TYPE="${2:-desktop}"
DISPLAY_NUM="${3:-}"

if [[ -z "$TASK_ID" ]]; then
    echo "Usage: $0 <task_id> [device_type] [display_num]"
    exit 1
fi

LOG_FILE="/var/log/vnc-debug/debug-session-${TASK_ID}.log"
mkdir -p "$(dirname "$LOG_FILE")"

case "$DEVICE_TYPE" in
    "mobile") RESOLUTION="900x1200" ;;
    "tablet") RESOLUTION="1280x1024" ;;
    *) RESOLUTION="1920x1080" ;;
esac

if [[ -z "$DISPLAY_NUM" ]]; then
    for i in {100..150}; do
        if ! pgrep -f ":$i" > /dev/null && [[ ! -f "/tmp/.X$i-lock" ]]; then
            DISPLAY_NUM=$i
            break
        fi
    done
fi

if [[ -z "$DISPLAY_NUM" ]]; then
    echo "Error: No free display found" >&2
    exit 1
fi

VNC_PORT=$((5900 + DISPLAY_NUM - 100))

echo "$(date) - Starting debug session for task $TASK_ID" >> "$LOG_FILE"

# Запускаем Xvfb
Xvfb ":$DISPLAY_NUM" -screen 0 "${RESOLUTION}x24" -nolisten tcp -dpi 96 +extension GLX +extension RANDR -noreset &
XVFB_PID=$!
sleep 3

# Запускаем VNC сервер
x11vnc -display ":$DISPLAY_NUM" -forever -nopw -localhost -rfbport "$VNC_PORT" -shared -nodpms -nomodtweak -quiet &
VNC_PID=$!
sleep 2

# Сохраняем PID'ы
echo "$XVFB_PID" > "/tmp/debug-xvfb-${TASK_ID}.pid"
echo "$VNC_PID" > "/tmp/debug-vnc-${TASK_ID}.pid"
echo "$DISPLAY_NUM" > "/tmp/debug-display-${TASK_ID}.num"

echo "Debug session started: Task $TASK_ID, Display :$DISPLAY_NUM, VNC port $VNC_PORT"
echo "Connect with: vncviewer localhost:$VNC_PORT"
