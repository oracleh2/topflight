#!/bin/bash

# PM2 Management script для TopFlight (совместимый с существующим)
# scripts/pm2-management.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKEND_DIR="$PROJECT_ROOT/backend"
ACTION=${1:-}

# Проверяем PM2
if ! command -v pm2 &> /dev/null; then
    echo "❌ PM2 not found. Installing..."
    npm install -g pm2
fi

case "$ACTION" in
    "start")
        echo "🚀 Starting TopFlight API with PM2..."
        cd "$BACKEND_DIR"

        # Активируем виртуальное окружение
        source venv/bin/activate

        # Запуск API сервера
        pm2 start run_api.py --name "topflight-api" --interpreter python

        # Запуск worker (опционально)
        if [ "${START_WORKER:-true}" = "true" ]; then
            pm2 start run_worker.py --name "topflight-worker" --interpreter python
        fi

        # Сохраняем конфигурацию PM2
        pm2 save

        echo "✅ TopFlight started with PM2"
        pm2 status
        ;;

    "stop")
        echo "🛑 Stopping TopFlight..."
        pm2 stop topflight-api topflight-worker || true
        echo "✅ TopFlight stopped"
        ;;

    "restart")
        echo "🔄 Restarting TopFlight..."
        pm2 restart topflight-api topflight-worker || true
        echo "✅ TopFlight restarted"
        ;;

    "status")
        echo "📊 TopFlight Status:"
        pm2 status
        ;;

    "logs")
        echo "📋 TopFlight Logs:"
        pm2 logs topflight-api
        ;;

    "monitor")
        echo "📊 Opening PM2 monitor..."
        pm2 monit
        ;;

    *)
        echo "TopFlight PM2 Management"
        echo "Usage: $0 {start|stop|restart|status|logs|monitor}"
        echo ""
        echo "Commands:"
        echo "  start    - Start TopFlight API and worker"
        echo "  stop     - Stop all TopFlight processes"
        echo "  restart  - Restart all TopFlight processes"
        echo "  status   - Show process status"
        echo "  logs     - Show API logs"
        echo "  monitor  - Open PM2 monitoring interface"
        exit 1
        ;;
esac
