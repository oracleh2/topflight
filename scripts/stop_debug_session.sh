#!/bin/bash
set -euo pipefail

TASK_ID="${1:-}"
if [[ -z "$TASK_ID" ]]; then
    echo "Usage: $0 <task_id>"
    exit 1
fi

# Останавливаем процессы
for type in vnc xvfb; do
    if [[ -f "/tmp/debug-${type}-${TASK_ID}.pid" ]]; then
        PID=$(cat "/tmp/debug-${type}-${TASK_ID}.pid")
        if kill -0 "$PID" 2>/dev/null; then
            kill "$PID" 2>/dev/null || true
            sleep 1
            kill -9 "$PID" 2>/dev/null || true
        fi
        rm -f "/tmp/debug-${type}-${TASK_ID}.pid"
    fi
done

# Очищаем дисплей
if [[ -f "/tmp/debug-display-${TASK_ID}.num" ]]; then
    DISPLAY_NUM=$(cat "/tmp/debug-display-${TASK_ID}.num")
    rm -f "/tmp/.X${DISPLAY_NUM}-lock" 2>/dev/null || true
    rm -f "/tmp/debug-display-${TASK_ID}.num"
fi

echo "Debug session stopped: Task $TASK_ID"
