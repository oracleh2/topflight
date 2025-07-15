# /app/scripts/vnc_emergency_cleanup.sh
#!/bin/bash
# Экстренная очистка всех VNC процессов

set -euo pipefail

echo "Emergency VNC cleanup started..."

# Убиваем все процессы VNC
echo "Killing all x11vnc processes..."
sudo pkill -f "x11vnc" || true

# Убиваем все Xvfb процессы (кроме :99 - основного)
echo "Killing debug Xvfb processes..."
for display in {100..199}; do
    if pgrep -f "Xvfb :$display" > /dev/null; then
        echo "Killing Xvfb :$display"
        sudo pkill -f "Xvfb :$display" || true
    fi
done

# Очищаем lock файлы
echo "Cleaning display lock files..."
sudo rm -f /tmp/.X*-lock
sudo rm -f /tmp/.X11-unix/X*

# Очищаем VNC сессии через API если доступно
if curl -f -s "http://localhost:8000/health" > /dev/null; then
    echo "Cleaning VNC sessions via API..."
    curl -s -X DELETE "http://localhost:8000/admin/debug/sessions/cleanup" \
        -H "Authorization: Bearer $ADMIN_TOKEN" || true
fi

echo "Emergency cleanup completed"
