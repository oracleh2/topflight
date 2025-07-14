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

    # Создаем пустые файлы логов если их нет (с префиксом backend-)
    touch "$LOGS_DIR/backend-api.log"
    touch "$LOGS_DIR/backend-api-out.log"
    touch "$LOGS_DIR/backend-api-error.log"
    touch "$LOGS_DIR/backend-worker.log"
    touch "$LOGS_DIR/backend-worker-out.log"
    touch "$LOGS_DIR/backend-worker-error.log"
    touch "$LOGS_DIR/backend-monitor.log"
    touch "$LOGS_DIR/backend-monitor-out.log"
    touch "$LOGS_DIR/backend-monitor-error.log"

    echo -e "${GREEN}✅ Файлы логов Backend подготовлены${NC}"
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

# Функция запуска Worker
start_worker() {
    echo -e "${BLUE}🚀 Запуск Yandex Parser Worker...${NC}"

    cd "$BACKEND_DIR" || exit 1

    # Активируем виртуальное окружение если есть
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
    fi

    # Запускаем через PM2
    pm2 start "$ECOSYSTEM_FILE" --only yandex-parser-worker

    echo -e "${GREEN}✅ Worker запущен!${NC}"
    echo -e "${BLUE}📊 Статус процессов:${NC}"
    pm2 status
}

# Функция запуска Monitor
start_monitor() {
    echo -e "${BLUE}🚀 Запуск Yandex Parser Monitor...${NC}"

    cd "$BACKEND_DIR" || exit 1

    # Активируем виртуальное окружение если есть
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
    fi

    # Запускаем через PM2
    pm2 start "$ECOSYSTEM_FILE" --only yandex-parser-monitor

    echo -e "${GREEN}✅ Monitor запущен!${NC}"
    echo -e "${BLUE}📊 Статус процессов:${NC}"
    pm2 status
}

# Функция запуска всех сервисов
start_all() {
    echo -e "${BLUE}🚀 Запуск всех Backend сервисов...${NC}"

    cd "$BACKEND_DIR" || exit 1

    # Активируем виртуальное окружение если есть
    if [ -d "venv" ]; then
        source venv/bin/activate
        echo -e "${GREEN}✅ Виртуальное окружение активировано${NC}"
    fi

    # Запускаем через PM2
    pm2 start "$ECOSYSTEM_FILE"

    echo -e "${GREEN}✅ Все Backend сервисы запущены!${NC}"
    echo -e "${BLUE}📊 Статус процессов:${NC}"
    pm2 status
}

# Функция остановки API
stop_api() {
    echo -e "${YELLOW}🛑 Остановка Yandex Parser API...${NC}"
    pm2 stop yandex-parser-api
    echo -e "${GREEN}✅ API остановлен${NC}"
}

# Функция остановки Worker
stop_worker() {
    echo -e "${YELLOW}🛑 Остановка Yandex Parser Worker...${NC}"
    pm2 stop yandex-parser-worker
    echo -e "${GREEN}✅ Worker остановлен${NC}"
}

# Функция остановки Monitor
stop_monitor() {
    echo -e "${YELLOW}🛑 Остановка Yandex Parser Monitor...${NC}"
    pm2 stop yandex-parser-monitor
    echo -e "${GREEN}✅ Monitor остановлен${NC}"
}

# Функция остановки всех сервисов
stop_all() {
    echo -e "${YELLOW}🛑 Остановка всех Backend сервисов...${NC}"
    pm2 stop yandex-parser-api yandex-parser-worker yandex-parser-monitor
    echo -e "${GREEN}✅ Все Backend сервисы остановлены${NC}"
}

# Функция перезапуска API
restart_api() {
    echo -e "${BLUE}🔄 Перезапуск Yandex Parser API...${NC}"
    pm2 restart yandex-parser-api
    echo -e "${GREEN}✅ API перезапущен${NC}"
}

# Функция перезапуска Worker
restart_worker() {
    echo -e "${BLUE}🔄 Перезапуск Yandex Parser Worker...${NC}"
    pm2 restart yandex-parser-worker
    echo -e "${GREEN}✅ Worker перезапущен${NC}"
}

# Функция перезапуска Monitor
restart_monitor() {
    echo -e "${BLUE}🔄 Перезапуск Yandex Parser Monitor...${NC}"
    pm2 restart yandex-parser-monitor
    echo -e "${GREEN}✅ Monitor перезапущен${NC}"
}

# Функция перезапуска всех сервисов
restart_all() {
    echo -e "${BLUE}🔄 Перезапуск всех Backend сервисов...${NC}"
    pm2 restart yandex-parser-api yandex-parser-worker yandex-parser-monitor
    echo -e "${GREEN}✅ Все Backend сервисы перезапущены${NC}"
}

# Функция поиска актуального файла лога (с учетом ротации PM2)
find_log_file() {
    local base_name="$1"

    # Сначала проверяем файл без суффикса
    if [ -f "$LOGS_DIR/$base_name" ] && [ -s "$LOGS_DIR/$base_name" ]; then
        echo "$LOGS_DIR/$base_name"
        return 0
    fi

    # Затем ищем файлы с суффиксами -0, -1, -2, etc.
    for i in {0..9}; do
        local file_with_suffix="$LOGS_DIR/${base_name%%.log}-${i}.log"
        if [ -f "$file_with_suffix" ]; then
            echo "$file_with_suffix"
            return 0
        fi
    done

    # Если ничего не найдено, возвращаем базовое имя
    echo "$LOGS_DIR/$base_name"
    return 1
}

# Функция просмотра логов
show_logs() {
    local actual_file
    case "$1" in
        "api")
            actual_file=$(find_log_file "backend-api.log")
            echo -e "${BLUE}📋 Логи API (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "api-out")
            actual_file=$(find_log_file "backend-api-out.log")
            echo -e "${BLUE}📋 Stdout логи API (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "api-error")
            actual_file=$(find_log_file "backend-api-error.log")
            echo -e "${RED}🚨 Error логи API (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "worker")
            actual_file=$(find_log_file "backend-worker.log")
            echo -e "${BLUE}📋 Логи Worker (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "worker-out")
            actual_file=$(find_log_file "backend-worker-out.log")
            echo -e "${BLUE}📋 Stdout логи Worker (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "worker-error")
            actual_file=$(find_log_file "backend-worker-error.log")
            echo -e "${RED}🚨 Error логи Worker (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "monitor")
            actual_file=$(find_log_file "backend-monitor.log")
            echo -e "${BLUE}📋 Логи Monitor (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "monitor-out")
            actual_file=$(find_log_file "backend-monitor-out.log")
            echo -e "${BLUE}📋 Stdout логи Monitor (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "monitor-error")
            actual_file=$(find_log_file "backend-monitor-error.log")
            echo -e "${RED}🚨 Error логи Monitor (последние 50 строк):${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -50 "$actual_file" 2>/dev/null || echo -e "${RED}❌ Файл не найден или пустой${NC}"
            ;;
        "all")
            echo -e "${BLUE}📋 Все логи Backend:${NC}"
            echo -e "${GREEN}--- API STDOUT ---${NC}"
            actual_file=$(find_log_file "backend-api-out.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            echo -e "${RED}--- API STDERR ---${NC}"
            actual_file=$(find_log_file "backend-api-error.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            echo -e "${BLUE}--- API COMBINED ---${NC}"
            actual_file=$(find_log_file "backend-api.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            ;;
        "errors")
            echo -e "${RED}🚨 Все ошибки Backend:${NC}"
            echo -e "${YELLOW}--- API ERRORS ---${NC}"
            actual_file=$(find_log_file "backend-api-error.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            echo -e "${YELLOW}--- WORKER ERRORS ---${NC}"
            actual_file=$(find_log_file "backend-worker-error.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            echo -e "${YELLOW}--- MONITOR ERRORS ---${NC}"
            actual_file=$(find_log_file "backend-monitor-error.log")
            echo -e "${PURPLE}$(basename "$actual_file")${NC}"
            tail -20 "$actual_file" 2>/dev/null || echo "Файл пустой"
            ;;
        *)
            echo -e "${YELLOW}Доступные логи: api, api-out, api-error, worker, worker-out, worker-error, monitor, monitor-out, monitor-error, all, errors${NC}"
            ;;
    esac
}

# Функция отслеживания логов в реальном времени
follow_logs() {
    local actual_file
    case "$1" in
        "api")
            actual_file=$(find_log_file "backend-api.log")
            echo -e "${BLUE}📡 Отслеживание логов API в реальном времени...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "api-out")
            actual_file=$(find_log_file "backend-api-out.log")
            echo -e "${BLUE}📡 Отслеживание stdout логов API...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "api-error")
            actual_file=$(find_log_file "backend-api-error.log")
            echo -e "${RED}📡 Отслеживание error логов API...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "worker")
            actual_file=$(find_log_file "backend-worker.log")
            echo -e "${BLUE}📡 Отслеживание логов Worker...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "worker-error")
            actual_file=$(find_log_file "backend-worker-error.log")
            echo -e "${RED}📡 Отслеживание error логов Worker...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "monitor")
            actual_file=$(find_log_file "backend-monitor.log")
            echo -e "${BLUE}📡 Отслеживание логов Monitor...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "monitor-error")
            actual_file=$(find_log_file "backend-monitor-error.log")
            echo -e "${RED}📡 Отслеживание error логов Monitor...${NC}"
            echo -e "${PURPLE}Файл: $(basename "$actual_file")${NC}"
            tail -f "$actual_file"
            ;;
        "all")
            echo -e "${BLUE}📡 Отслеживание всех Backend логов...${NC}"
            # Находим все актуальные файлы
            local api_file=$(find_log_file "backend-api.log")
            local api_out_file=$(find_log_file "backend-api-out.log")
            local api_error_file=$(find_log_file "backend-api-error.log")
            echo -e "${PURPLE}Файлы: $(basename "$api_file"), $(basename "$api_out_file"), $(basename "$api_error_file")${NC}"
            tail -f "$api_file" "$api_out_file" "$api_error_file"
            ;;
        "errors")
            echo -e "${RED}📡 Отслеживание всех error логов Backend...${NC}"
            # Находим все error файлы
            local api_error_file=$(find_log_file "backend-api-error.log")
            local worker_error_file=$(find_log_file "backend-worker-error.log")
            local monitor_error_file=$(find_log_file "backend-monitor-error.log")
            echo -e "${PURPLE}Файлы: $(basename "$api_error_file"), $(basename "$worker_error_file"), $(basename "$monitor_error_file")${NC}"
            tail -f "$api_error_file" "$worker_error_file" "$monitor_error_file"
            ;;
        *)
            echo -e "${YELLOW}Доступные логи для отслеживания: api, api-out, api-error, worker, worker-error, monitor, monitor-error, all, errors${NC}"
            ;;
    esac
}

# Функция очистки логов
clear_logs() {
    echo -e "${YELLOW}🧹 Очистка Backend логов...${NC}"

    # Создаем директорию для архивов если её нет
    mkdir -p "/var/www/topflight/logs_archives"

    # Создаем архив старых логов
    ARCHIVE_NAME="backend_logs_backup_$(date +%Y%m%d_%H%M%S).tar.gz"
    cd "/var/www/topflight" || exit 1
    tar -czf "logs_archives/$ARCHIVE_NAME" logs/backend-*.log

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

    echo -e "${GREEN}✅ Backend логи очищены, архив создан: $ARCHIVE_NAME${NC}"
}

# Функция мониторинга
monitor() {
    echo -e "${BLUE}📊 Мониторинг Backend процессов:${NC}"
    pm2 monit
}

# Главная функция
main() {
    case "$1" in
        "init")
            create_logs_dir
            ;;
        "start")
            case "$2" in
                "api")
                    create_logs_dir
                    start_api
                    ;;
                "worker")
                    create_logs_dir
                    start_worker
                    ;;
                "monitor")
                    create_logs_dir
                    start_monitor
                    ;;
                "all"|"")
                    create_logs_dir
                    start_all
                    ;;
                *)
                    echo -e "${RED}❌ Неизвестный сервис: $2${NC}"
                    echo -e "${YELLOW}Доступные сервисы: api, worker, monitor, all${NC}"
                    ;;
            esac
            ;;
        "stop")
            case "$2" in
                "api")
                    stop_api
                    ;;
                "worker")
                    stop_worker
                    ;;
                "monitor")
                    stop_monitor
                    ;;
                "all"|"")
                    stop_all
                    ;;
                *)
                    echo -e "${RED}❌ Неизвестный сервис: $2${NC}"
                    echo -e "${YELLOW}Доступные сервисы: api, worker, monitor, all${NC}"
                    ;;
            esac
            ;;
        "restart")
            case "$2" in
                "api")
                    restart_api
                    ;;
                "worker")
                    restart_worker
                    ;;
                "monitor")
                    restart_monitor
                    ;;
                "all"|"")
                    restart_all
                    ;;
                *)
                    echo -e "${RED}❌ Неизвестный сервис: $2${NC}"
                    echo -e "${YELLOW}Доступные сервисы: api, worker, monitor, all${NC}"
                    ;;
            esac
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
            echo -e "${BLUE}🔧 Yandex Parser Backend Management${NC}"
            echo ""
            echo -e "${GREEN}Доступные команды:${NC}"
            echo "  init                    - Создать директории и файлы логов"
            echo "  start [service]         - Запустить сервис (api|worker|monitor|all)"
            echo "  stop [service]          - Остановить сервис (api|worker|monitor|all)"
            echo "  restart [service]       - Перезапустить сервис (api|worker|monitor|all)"
            echo "  status                  - Показать статус процессов"
            echo "  logs [type]             - Показать логи"
            echo "  follow [type]           - Отслеживать логи в реальном времени"
            echo "  clear-logs              - Очистить логи (с архивированием)"
            echo "  monitor                 - Открыть PM2 мониторинг"
            echo ""
            echo -e "${YELLOW}Типы логов:${NC}"
            echo "  api, api-out, api-error, worker, worker-out, worker-error,"
            echo "  monitor, monitor-out, monitor-error, all, errors"
            echo ""
            echo -e "${YELLOW}Примеры:${NC}"
            echo "  ./pm2-management.sh start api"
            echo "  ./pm2-management.sh logs api-error"
            echo "  ./pm2-management.sh follow api-error"
            echo "  ./pm2-management.sh restart all"
            ;;
    esac
}

# Запуск скрипта
main "$@"
