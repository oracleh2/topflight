# Создаем конфигурационный файл
sudo tee vnc_config.js > /dev/null << 'EOF'
// Конфигурация noVNC для интеграции с нашей системой
(function() {
    'use strict';

    // Получаем параметры VNC из URL или API
    function getVNCConfig() {
        const urlParams = new URLSearchParams(window.location.search);
        const host = urlParams.get('host') || '127.0.0.1';
        const port = urlParams.get('port') || '5900';
        const taskId = urlParams.get('task_id');

        return {
            host: host,
            port: parseInt(port),
            encrypt: window.location.protocol === 'https:',
            path: 'websockify',
            taskId: taskId
        };
    }

    // Автоматическое подключение при загрузке страницы
    function autoConnect() {
        const config = getVNCConfig();

        if (window.vnc) {
            // Настраиваем подключение
            window.vnc.connect(`ws://${config.host}:${config.port}/${config.path}`);

            // Отображаем информацию о сессии
            if (config.taskId) {
                const infoDiv = document.createElement('div');
                infoDiv.innerHTML = `
                    <div style="background: #2196F3; color: white; padding: 10px; margin: 10px; border-radius: 4px;">
                        <strong>Debug Session:</strong> Task ID ${config.taskId}
                        <br>
                        <strong>VNC:</strong> ${config.host}:${config.port}
                    </div>
                `;
                document.body.insertBefore(infoDiv, document.body.firstChild);
            }
        }
    }

    // Запускаем после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoConnect);
    } else {
        autoConnect();
    }
})();
EOF

# Создаем обертку для websockify
sudo tee websockify_wrapper.sh > /dev/null << 'EOF'
#!/bin/bash
# Обертка для запуска websockify с множественными VNC серверами

WEBSOCKIFY_PORT=6080
LOG_FILE="/var/log/websockify.log"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log "Starting websockify proxy on port $WEBSOCKIFY_PORT"

# Запускаем websockify с поддержкой токенов
exec /opt/novnc/noVNC/utils/websockify/websockify.py \
    --web /opt/novnc/noVNC \
    --token-plugin TokenFile \
    --token-source /tmp/vnc_tokens.conf \
    --port "$WEBSOCKIFY_PORT" \
    --verbose
EOF

sudo chmod +x websockify_wrapper.sh

# Создаем systemd сервис для websockify
sudo tee /etc/systemd/system/websockify.service > /dev/null << 'EOF'
[Unit]
Description=WebSocket to TCP proxy for noVNC
After=network.target

[Service]
Type=simple
User=parser
Group=parser
WorkingDirectory=/opt/novnc/noVNC
ExecStart=/opt/novnc/noVNC/websockify_wrapper.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ресурсы
MemoryLimit=256M
CPUQuota=20%

[Install]
WantedBy=multi-user.target
EOF

# Создаем файл токенов для VNC сессий
sudo touch /tmp/vnc_tokens.conf
sudo chown parser:parser /tmp/vnc_tokens.conf

# Включаем и запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable websockify.service
sudo systemctl start websockify.service

echo "noVNC setup completed"
echo "Web interface available at: http://localhost:6080/vnc_lite.html"
echo "Token file: /tmp/vnc_tokens.conf"

# Создаем конфигурационный файл
sudo tee vnc_config.js > /dev/null << 'EOF'
// Конфигурация noVNC для интеграции с нашей системой
(function() {
    'use strict';

    // Получаем параметры VNC из URL или API
    function getVNCConfig() {
        const urlParams = new URLSearchParams(window.location.search);
        const host = urlParams.get('host') || '127.0.0.1';
        const port = urlParams.get('port') || '5900';
        const taskId = urlParams.get('task_id');

        return {
            host: host,
            port: parseInt(port),
            encrypt: window.location.protocol === 'https:',
            path: 'websockify',
            taskId: taskId
        };
    }

    // Автоматическое подключение при загрузке страницы
    function autoConnect() {
        const config = getVNCConfig();

        if (window.vnc) {
            // Настраиваем подключение
            window.vnc.connect(`ws://${config.host}:${config.port}/${config.path}`);

            // Отображаем информацию о сессии
            if (config.taskId) {
                const infoDiv = document.createElement('div');
                infoDiv.innerHTML = `
                    <div style="background: #2196F3; color: white; padding: 10px; margin: 10px; border-radius: 4px;">
                        <strong>Debug Session:</strong> Task ID ${config.taskId}
                        <br>
                        <strong>VNC:</strong> ${config.host}:${config.port}
                    </div>
                `;
                document.body.insertBefore(infoDiv, document.body.firstChild);
            }
        }
    }

    // Запускаем после загрузки DOM
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', autoConnect);
    } else {
        autoConnect();
    }
})();
EOF

# Создаем обертку для websockify
sudo tee websockify_wrapper.sh > /dev/null << 'EOF'
#!/bin/bash
# Обертка для запуска websockify с множественными VNC серверами

WEBSOCKIFY_PORT=6080
LOG_FILE="/var/log/websockify.log"

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

log "Starting websockify proxy on port $WEBSOCKIFY_PORT"

# Запускаем websockify с поддержкой токенов
exec /opt/novnc/noVNC/utils/websockify/websockify.py \
    --web /opt/novnc/noVNC \
    --token-plugin TokenFile \
    --token-source /tmp/vnc_tokens.conf \
    --port "$WEBSOCKIFY_PORT" \
    --verbose
EOF

sudo chmod +x websockify_wrapper.sh

# Создаем systemd сервис для websockify
sudo tee /etc/systemd/system/websockify.service > /dev/null << 'EOF'
[Unit]
Description=WebSocket to TCP proxy for noVNC
After=network.target

[Service]
Type=simple
User=parser
Group=parser
WorkingDirectory=/opt/novnc/noVNC
ExecStart=/opt/novnc/noVNC/websockify_wrapper.sh
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ресурсы
MemoryLimit=256M
CPUQuota=20%

[Install]
WantedBy=multi-user.target
EOF

# Создаем файл токенов для VNC сессий
sudo touch /tmp/vnc_tokens.conf
sudo chown parser:parser /tmp/vnc_tokens.conf

# Включаем и запускаем сервис
sudo systemctl daemon-reload
sudo systemctl enable websockify.service
sudo systemctl start websockify.service

echo "noVNC setup completed"
echo "Web interface available at: http://localhost:6080/vnc_lite.html"
echo "Token file: /tmp/vnc_tokens.conf"
