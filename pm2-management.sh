#!/bin/bash
# pm2-management.sh

# Цвета для вывода
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Базовые пути
BACKEND_DIR="/var/www/topflight/backend"
LOGS_DIR="/var/www/topflight/logs"
ECOSYSTEM_FILE="/var/www/topflight/ecosystem.config.js"

# Функция для создания директории логов
create_logs_dir() {
    echo -e "${BLUE}🗂️  Создание директории для логов...${NC}"

    if [ ! -d "$LOGS_DIR" ]; then
        mkdir -p "$LOGS_DIR"
        echo -e "${GREEN}✅ Директория логов создана: $LOGS_DIR${NC}"
    else
        echo -e "${YELLOW}⚠️  Директория логов уже существует: $LOGS_DIR${NC}"
    fi

    # Устанавливаем права доступа
    chmod 755 "$LOGS_DIR"

    # Создаем пустые файлы логов если их нет
    touch "$LOGS_DIR/api.log"
    touch "$LOGS_DIR/api-out.log"
    touch "$LOGS_DIR/api-error.log"
    touch "$LOGS_DIR/worker.log"
    touch "$LOGS_DIR/worker-out.log"
    touch "$LOGS_DIR/worker-error.log"
    touch "$LOGS_DIR/monitor.log"
    touch "$LOGS_DIR/monitor-out.log"
    touch "$LOGS_DIR/monitor-error.log"

    echo -e "${GREEN}✅ Файлы логов подготовлены${NC}"
}

# Функция запуска API
start_api() {
    echo -e "${BLUE}🚀 Запуск Yandex Parser API...${NC}"

    cd "$BACKEND_DIR" || exit 1

    # Активируем виртуальное окружение если есть
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
    fi

    # Запускаем через PM2
    pm2 start "$ECOSYSTEM_FILE" --only yandex-parser-api

    echo -e "${GREEN}✅ API запущен!${NC}"
    echo -e "${BLUE}📊 Статус процессов:${NC}"
    pm2 status
}

# Функция остановки API
stop_api() {
    echo -e "${YELLOW}🛑 Остановка Yandex Parser API...${NC}"
    pm2 stop yandex-parser-api
    echo -e "${GREEN}✅ API остановлен${NC}"
}

# Функция перезапуска API
restart_api() {
    echo -e "${BLUE}🔄 Перезапуск Yandex Parser API...${NC}"
    pm2 restart yandex-parser-api
    echo -e "${GREEN}✅ API перезапущен${NC}"
}

# Функция просмотра логов
show_logs() {
    case "$1" in
        "api")
            echo -e "${BLUE}📋 Логи API (последние 50 строк):${NC}"
            tail -50 "$LOGS_DIR/api.log"
            ;;
        "api-out")
            echo -e "${BLUE}📋 Stdout логи API (последние 50 строк):${NC}"
            tail -50 "$LOGS_DIR/api-out.log"
            ;;
        "api-error")
            echo -e "${RED}🚨 Error логи API (последние 50 строк):${NC}"
            tail -50 "$LOGS_DIR/api-error.log"
            ;;
        "all")
            echo -e "${BLUE}📋 Все логи API:${NC}"
            echo -e "${GREEN}--- STDOUT ---${NC}"
            tail -20 "$LOGS_DIR/api-out.log"
            echo -e "${RED}--- STDERR ---${NC}"
            tail -20 "$LOGS_DIR/api-error.log"
            echo -e "${BLUE}--- COMBINED ---${NC}"
            tail -20 "$LOGS_DIR/api.log"
            ;;
        *)
            echo -e "${YELLOW}Доступные логи: api, api-out, api-error, all${NC}"
            ;;
    esac
}

# Функция отслеживания логов в реальном времени
follow_logs() {
    case "$1" in
        "api")
            echo -e "${BLUE}📡 Отслеживание логов API в реальном времени...${NC}"
            tail -f "$LOGS_DIR/api.log"
            ;;
        "api-out")
            echo -e "${BLUE}📡 Отслеживание stdout логов API...${NC}"
            tail -f "$LOGS_DIR/api-out.log"
            ;;
        "api-error")
            echo -e "${RED}📡 Отслеживание error логов API...${NC}"
            tail -f "$LOGS_DIR/api-error.log"
            ;;
        *)
            echo -e "${YELLOW}Доступные логи для отслеживания: api, api-out, api-error${NC}"
            ;;
    esac
}

# Функция очистки логов
clear_logs() {
    echo -e "${YELLOW}🧹 Очистка логов...${NC}"

    # Создаем архив старых логов
    ARCHIVE_NAME="logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    cd "$BACKEND_DIR" || exit 1
    tar -czf "logs_archives/$ARCHIVE_NAME" logs/

    # Очищаем текущие логи
    > "$LOGS_DIR/backend-api.log"
    > "$LOGS_DIR/backend-api-out.log"
    > "$LOGS_DIR/backend-api-error.log"
    > "$LOGS_DIR/backend-worker.log"
    > "$LOGS_DIR/backend-worker-out.log"
    > "$LOGS_DIR/backend-worker-error.log"
    > "$LOGS_DIR/backend-monitor.log"
    > "$LOGS_DIR/backend-monitor-out.log"
    > "$LOGS_DIR/backend-monitor-error.log"

    echo -e "${GREEN}✅ Логи очищены, архив создан: $ARCHIVE_NAME${NC}"
}

# Функция мониторинга
monitor() {
    echo -e "${BLUE}📊 Мониторинг процессов:${NC}"
    pm2 monit
}

# Главная функция
main() {
    case "$1" in
        "init")
            create_logs_dir
            ;;
        "start")
            create_logs_dir
            start_api
            ;;
        "stop")
            stop_api
            ;;
        "restart")
            restart_api
            ;;
        "status")
            pm2 status
            ;;
        "logs")
            show_logs "$2"
            ;;
        "follow")
            follow_logs "$2"
            ;;
        "clear-logs")
            clear_logs
            ;;
        "monitor")
            monitor
            ;;
        *)
            echo -e "${BLUE}🔧 Yandex Parser API Management${NC}"
            echo ""
            echo -e "${GREEN}Доступные команды:${NC}"
            echo "  init        - Создать директории и файлы логов"
            echo "  start       - Запустить API"
            echo "  stop        - Остановить API"
            echo "  restart     - Перезапустить API"
            echo "  status      - Показать статус процессов"
            echo "  logs [type] - Показать логи (api|api-out|api-error|all)"
            echo "  follow [type] - Отслеживать логи в реальном времени"
            echo "  clear-logs  - Очистить логи (с архивированием)"
            echo "  monitor     - Открыть PM2 мониторинг"
            echo ""
            echo -e "${YELLOW}Примеры:${NC}"
            echo "  ./pm2-management.sh start"
            echo "  ./pm2-management.sh logs api-error"
            echo "  ./pm2-management.sh follow api"
            ;;
    esac
}

# Запуск скрипта
main "$@"
