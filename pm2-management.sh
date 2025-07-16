#!/bin/bash

# PM2 Management script для TopFlight с поддержкой VNC
# pm2-management.sh - Обновленный для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKEND_DIR="$PROJECT_ROOT/backend"
FRONTEND_DIR="$PROJECT_ROOT/frontend"
ACTION=${1:-}

# Функция для проверки окружения
check_environment() {
    # Проверяем что мы в правильной директории
    if [ ! -d "$PROJECT_ROOT" ]; then
        echo "❌ Project directory $PROJECT_ROOT not found!"
        echo "Please ensure you're running this on the correct server"
        exit 1
    fi

    if [ ! -d "$BACKEND_DIR" ]; then
        echo "❌ Backend directory $BACKEND_DIR not found!"
        exit 1
    fi

    # Проверяем PM2
    if ! command -v pm2 &> /dev/null; then
        echo "📦 PM2 not found. Installing..."
        npm install -g pm2
    fi

    # Проверяем виртуальное окружение
    if [ ! -f "$BACKEND_DIR/venv/bin/python" ]; then
        echo "❌ Python virtual environment not found at $BACKEND_DIR/venv"
        echo "Run: cd $BACKEND_DIR && python3.11 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
        exit 1
    fi

    # Проверяем Xvfb
    if ! systemctl is-active --quiet xvfb-main 2>/dev/null && ! systemctl is-active --quiet xvfb 2>/dev/null; then
        echo "⚠️ Xvfb service not running. VNC debugging may not work."
        echo "Run: sudo systemctl start xvfb-main"
    fi
}

# Функция для настройки environment переменных
setup_environment() {
    cd "$BACKEND_DIR"

    # Устанавливаем переменные окружения для TopFlight
    export PROJECT_ROOT="$PROJECT_ROOT"
    export DISPLAY=":99"
    export PYTHONPATH="$BACKEND_DIR"

    # Загружаем .env файл если существует
    if [ -f "$BACKEND_DIR/.env" ]; then
        set -a  # автоэкспорт переменных
        source "$BACKEND_DIR/.env"
        set +a
    else
        echo "⚠️ .env file not found. Using default settings."
    fi
}

case "$ACTION" in
    "start")
        echo "🚀 Starting TopFlight with PM2..."
        check_environment
        setup_environment

        cd "$BACKEND_DIR"

        # Активируем виртуальное окружение
        source venv/bin/activate

        # Проверяем базу данных
        echo "🔍 Checking database connection..."
        if ! python -c "from app.database import test_connection; test_connection()" 2>/dev/null; then
            echo "⚠️ Database connection failed. Please check your settings."
        fi

        # Запуск API сервера
        echo "🌐 Starting API server..."
        pm2 start run_api.py --name "topflight-api" \
            --interpreter "$BACKEND_DIR/venv/bin/python" \
            --cwd "$BACKEND_DIR" \
            --log "$PROJECT_ROOT/logs/backend-api.log" \
            --error "$PROJECT_ROOT/logs/backend-api.error.log" \
            --env PROJECT_ROOT="$PROJECT_ROOT" \
            --env DISPLAY=":99" \
            --env PYTHONPATH="$BACKEND_DIR"

        # Запуск worker (опционально)
        if [ "${START_WORKER:-true}" = "true" ]; then
            echo "⚙️ Starting worker..."
            pm2 start run_worker.py --name "topflight-worker" \
                --interpreter "$BACKEND_DIR/venv/bin/python" \
                --cwd "$BACKEND_DIR" \
                --log "$PROJECT_ROOT/logs/worker.log" \
                --error "$PROJECT_ROOT/logs/worker.error.log" \
                --env PROJECT_ROOT="$PROJECT_ROOT" \
                --env DISPLAY=":99" \
                --env PYTHONPATH="$BACKEND_DIR"
        fi

        # Запуск фронтэнда (опционально)
        if [ "${START_FRONTEND:-true}" = "true" ]; then
            echo "🎨 Starting frontend..."

            # Проверяем существование директории фронтэнда
            if [ ! -d "$FRONTEND_DIR" ]; then
                echo "⚠️ Frontend directory $FRONTEND_DIR not found. Skipping frontend startup."
            else
                cd "$FRONTEND_DIR"

                # Проверяем package.json
                if [ ! -f "package.json" ]; then
                    echo "⚠️ package.json not found in frontend directory. Skipping frontend startup."
                else
                    # Проверяем node_modules
                    if [ ! -d "node_modules" ]; then
                        echo "📦 Installing frontend dependencies..."
                        npm install
                    fi

                    # Запускаем фронтэнд через PM2
                    echo "🎯 Starting frontend dev server..."
                    pm2 start npm --name "topflight-frontend" \
                        --cwd "$FRONTEND_DIR" \
                        --log "$PROJECT_ROOT/logs/frontend.log" \
                        --error "$PROJECT_ROOT/logs/frontend.error.log" \
                        -- run dev
                fi
            fi
        fi

        # Сохраняем конфигурацию PM2
        pm2 save

        echo "✅ TopFlight started with PM2"
        echo "📊 Status:"
        pm2 status

        echo ""
        echo "🔗 Access URLs:"
        echo "  API: http://localhost:8000"
        echo "  Health: http://localhost:8000/health"
        echo "  Docs: http://localhost:8000/docs"
        echo "  Admin: http://localhost:8000/admin"
        ;;

    "stop")
        echo "🛑 Stopping TopFlight..."
        pm2 stop topflight-api topflight-worker topflight-frontend 2>/dev/null || true
        echo "✅ TopFlight stopped"
        ;;

    "restart")
        echo "🔄 Restarting TopFlight..."
        setup_environment
        pm2 restart topflight-api topflight-worker 2>/dev/null || true
        echo "✅ TopFlight restarted"
        pm2 status
        ;;

    "status")
        echo "📊 TopFlight Status:"
        pm2 status

        echo ""
        echo "🔧 System Status:"
        echo "Project Root: $PROJECT_ROOT"

        # Проверка Xvfb
        if systemctl is-active --quiet xvfb-main 2>/dev/null; then
            echo "✅ Xvfb Main: RUNNING"
        elif systemctl is-active --quiet xvfb 2>/dev/null; then
            echo "✅ Xvfb: RUNNING"
        else
            echo "❌ Xvfb: NOT RUNNING"
        fi

        # Проверка VNC cleanup
        if systemctl is-active --quiet vnc-cleanup 2>/dev/null; then
            echo "✅ VNC Cleanup: RUNNING"
        else
            echo "⚠️ VNC Cleanup: NOT RUNNING"
        fi

        # Проверка API
        if curl -f -s "http://localhost:8000/health" >/dev/null 2>&1; then
            echo "✅ API Health: OK"
        else
            echo "❌ API Health: FAILED"
        fi
        ;;

    "logs")
        echo "📋 TopFlight Logs:"
        pm2 logs topflight-api --lines 50
        ;;

    "logs-worker")
        echo "📋 Worker Logs:"
        pm2 logs topflight-worker --lines 50
        ;;

    "logs-all")
        echo "📋 All TopFlight Logs:"
        pm2 logs --lines 50
        ;;

    "monitor")
        echo "📊 Opening PM2 monitor..."
        pm2 monit
        ;;

    "vnc-status")
        echo "🖥️ VNC System Status:"

        # Активные VNC сессии
        if [ -n "${ADMIN_TOKEN:-}" ]; then
            echo "Active VNC sessions:"
            curl -s -H "Authorization: Bearer $ADMIN_TOKEN" \
                 "http://localhost:8000/admin/debug/sessions" | jq '.' 2>/dev/null || echo "Could not fetch VNC sessions"
        else
            echo "⚠️ ADMIN_TOKEN not set. Cannot check VNC sessions."
            echo "Set ADMIN_TOKEN environment variable to check VNC status."
        fi

        # Процессы VNC
        echo ""
        echo "VNC Processes:"
        pgrep -fl "x11vnc" || echo "No VNC processes found"

        # Порты VNC
        echo ""
        echo "VNC Ports:"
        netstat -tlnp 2>/dev/null | grep ":590[0-9]" || echo "No VNC ports listening"
        ;;

    "debug")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 debug TASK_ID [DEVICE_TYPE]"
            echo "Example: $0 debug uuid-here desktop"
            exit 1
        fi

        TASK_ID="$2"
        DEVICE_TYPE="${3:-desktop}"

        if [ -z "${ADMIN_TOKEN:-}" ]; then
            echo "❌ ADMIN_TOKEN environment variable not set"
            echo "Please set ADMIN_TOKEN to use debug functionality"
            exit 1
        fi

        echo "🐛 Starting debug session for task: $TASK_ID"

        RESPONSE=$(curl -s -X POST \
            "http://localhost:8000/admin/debug/start/$TASK_ID?device_type=$DEVICE_TYPE" \
            -H "Authorization: Bearer $ADMIN_TOKEN" \
            -H "Content-Type: application/json")

        if echo "$RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
            VNC_PORT=$(echo "$RESPONSE" | jq -r '.debug_info.vnc_port // empty')
            WEB_VNC_URL=$(echo "$RESPONSE" | jq -r '.debug_info.web_vnc_url // empty')

            echo "✅ Debug session started successfully!"

            if [ -n "$VNC_PORT" ]; then
                echo "🖥️ VNC: vncviewer localhost:$VNC_PORT"
            fi

            if [ -n "$WEB_VNC_URL" ]; then
                echo "🌐 Web VNC: $WEB_VNC_URL"
            fi
        else
            ERROR=$(echo "$RESPONSE" | jq -r '.detail // "Unknown error"')
            echo "❌ Failed to start debug session: $ERROR"
            exit 1
        fi
        ;;

    "stop-debug")
        if [ -z "${2:-}" ]; then
            echo "Usage: $0 stop-debug TASK_ID"
            exit 1
        fi

        TASK_ID="$2"

        if [ -z "${ADMIN_TOKEN:-}" ]; then
            echo "❌ ADMIN_TOKEN environment variable not set"
            exit 1
        fi

        echo "🛑 Stopping debug session for task: $TASK_ID"

        RESPONSE=$(curl -s -X POST \
            "http://localhost:8000/admin/debug/stop/$TASK_ID" \
            -H "Authorization: Bearer $ADMIN_TOKEN" \
            -H "Content-Type: application/json")

        if echo "$RESPONSE" | jq -e '.success' >/dev/null 2>&1; then
            echo "✅ Debug session stopped successfully!"
        else
            ERROR=$(echo "$RESPONSE" | jq -r '.detail // "Unknown error"')
            echo "❌ Failed to stop debug session: $ERROR"
            exit 1
        fi
        ;;

    *)
        echo "TopFlight PM2 Management"
        echo "Usage: $0 {COMMAND} [OPTIONS]"
        echo ""
        echo "Main Commands:"
        echo "  start         - Start TopFlight API and worker"
        echo "  stop          - Stop all TopFlight processes"
        echo "  restart       - Restart all TopFlight processes"
        echo "  status        - Show process and system status"
        echo ""
        echo "Logging Commands:"
        echo "  logs          - Show API logs"
        echo "  logs-worker   - Show worker logs"
        echo "  logs-all      - Show all logs"
        echo "  monitor       - Open PM2 monitoring interface"
        echo ""
        echo "VNC Debug Commands:"
        echo "  vnc-status    - Show VNC system status"
        echo "  debug TASK_ID [TYPE]  - Start debug session"
        echo "  stop-debug TASK_ID    - Stop debug session"
        echo ""
        echo "Environment Variables:"
        echo "  START_WORKER  - Start worker process (default: true)"
        echo "  ADMIN_TOKEN   - Required for VNC debug commands"
        echo "  PROJECT_ROOT  - Project root path (default: /var/www/topflight)"
        echo ""
        echo "Examples:"
        echo "  $0 start                    # Start all services"
        echo "  START_WORKER=false $0 start # Start only API"
        echo "  $0 debug uuid-123 desktop   # Start debug session"
        echo "  $0 vnc-status              # Check VNC status"
        exit 1
        ;;
esac
