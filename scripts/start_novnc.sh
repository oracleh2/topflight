#!/bin/bash
# Запуск noVNC для VNC сессий

cd /var/www/noVNC

# Запускаем noVNC на порту 6080 для VNC порта 5900
./utils/novnc_proxy --vnc localhost:5900 --listen 6080 &
echo "noVNC started on http://localhost:6080"

# Можно добавить дополнительные порты для других VNC сессий
# ./utils/novnc_proxy --vnc localhost:5901 --listen 6081 &
# ./utils/novnc_proxy --vnc localhost:5902 --listen 6082 &

echo "noVNC web interface available at:"
echo "- http://localhost:6080 (VNC port 5900)"
echo "- http://localhost:6081 (VNC port 5901)"
echo "- http://localhost:6082 (VNC port 5902)"
