# docker/websockify/websockify_start.sh
#!/bin/bash
set -e

WEBSOCKIFY_PORT=${WEBSOCKIFY_PORT:-6081}
TOKEN_FILE=${TOKEN_FILE:-/app/tokens/vnc_tokens.conf}
LOG_FILE="/app/logs/websockify.log"

echo "Starting WebSockify on port $WEBSOCKIFY_PORT"
echo "Token file: $TOKEN_FILE"

# Создаем файл токенов если не существует
touch "$TOKEN_FILE"

# Запускаем websockify с поддержкой токенов
exec python websockify.py \
    --web /app/websockify \
    --token-plugin TokenFile \
    --token-source "$TOKEN_FILE" \
    --port "$WEBSOCKIFY_PORT" \
    --verbose \
    --log-file "$LOG_FILE"

