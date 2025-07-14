#!/bin/bash
# log-viewer.sh

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

LOGS_DIR="/var/www/topflight/logs"

# Функция красивого вывода логов с подсветкой
pretty_logs() {
    local file="$1"
    local lines="${2:-50}"

    if [ ! -f "$file" ]; then
        echo -e "${RED}❌ Файл логов не найден: $file${NC}"
        return 1
    fi

    echo -e "${BLUE}📋 Последние $lines строк из $(basename "$file"):${NC}"
    echo -e "${PURPLE}$file${NC}"
    echo "$(printf '=%.0s' {1..80})"

    # Подсвечиваем разные типы сообщений
    tail -"$lines" "$file" | while IFS= read -r line; do
        if [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"error"* ]] || [[ "$line" == *"Error"* ]]; then
            echo -e "${RED}$line${NC}"
        elif [[ "$line" == *"WARNING"* ]] || [[ "$line" == *"warning"* ]] || [[ "$line" == *"Warning"* ]]; then
            echo -e "${YELLOW}$line${NC}"
        elif [[ "$line" == *"INFO"* ]] || [[ "$line" == *"info"* ]] || [[ "$line" == *"Info"* ]]; then
            echo -e "${GREEN}$line${NC}"
        elif [[ "$line" == *"DEBUG"* ]] || [[ "$line" == *"debug"* ]] || [[ "$line" == *"Debug"* ]]; then
            echo -e "${CYAN}$line${NC}"
        else
            echo "$line"
        fi
    done

    echo "$(printf '=%.0s' {1..80})"
    echo ""
}

# Функция интерактивного просмотра логов
interactive_viewer() {
    while true; do
        clear
        echo -e "${BLUE}🔍 Интерактивный просмотрщик логов${NC}"
        echo "$(printf '=%.0s' {1..50})"
        echo ""
        echo -e "${GREEN}Доступные логи:${NC}"
        echo "1) API общие логи (backend-api.log)"
        echo "2) API stdout (backend-api-out.log)"
        echo "3) API ошибки (backend-api-error.log)"
        echo "4) Worker логи (backend-worker.log)"
        echo "5) Worker stdout (backend-worker-out.log)"
        echo "6) Worker ошибки (backend-worker-error.log)"
        echo "7) Все ошибки (error логи)"
        echo "8) Статистика файлов логов"
        echo "9) Очистить экран"
        echo "0) Выход"
        echo ""

        read -p "Выберите опцию (0-9): " choice

        case $choice in
            1)
                pretty_logs "$LOGS_DIR/backend-api.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            2)
                pretty_logs "$LOGS_DIR/backend-api-out.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            3)
                pretty_logs "$LOGS_DIR/backend-api-error.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            4)
                pretty_logs "$LOGS_DIR/backend-worker.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            5)
                pretty_logs "$LOGS_DIR/backend-worker-out.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            6)
                pretty_logs "$LOGS_DIR/backend-worker-error.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            7)
                echo -e "${RED}🚨 Все ошибки:${NC}"
                echo ""
                echo -e "${YELLOW}API Ошибки:${NC}"
                pretty_logs "$LOGS_DIR/backend-api-error.log" 20
                echo -e "${YELLOW}Worker Ошибки:${NC}"
                pretty_logs "$LOGS_DIR/backend-worker-error.log" 20
                read -p "Нажмите Enter для продолжения..."
                ;;
            8)
                show_log_stats
                read -p "Нажмите Enter для продолжения..."
                ;;
            9)
                clear
                ;;
            0)
                echo -e "${GREEN}👋 До свидания!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}❌ Неверный выбор. Попробуйте снова.${NC}"
                sleep 1
                ;;
        esac
    done
}

# Функция показа статистики логов
show_log_stats() {
    echo -e "${BLUE}📊 Статистика файлов логов:${NC}"
    echo "$(printf '=%.0s' {1..60})"

    for log_file in "$LOGS_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            local filename=$(basename "$log_file")
            local size=$(du -h "$log_file" | cut -f1)
            local lines=$(wc -l < "$log_file")
            local modified=$(stat -c %y "$log_file" | cut -d' ' -f1,2 | cut -d'.' -f1)

            echo -e "${GREEN}📄 $filename${NC}"
            echo "   Размер: $size"
            echo "   Строк: $lines"
            echo "   Изменен: $modified"
            echo ""
        fi
    done
}

# Функция поиска в логах
search_logs() {
    local pattern="$1"
    local context="${2:-3}"

    if [ -z "$pattern" ]; then
        echo -e "${RED}❌ Укажите паттерн для поиска${NC}"
        echo "Использование: $0 search 'error pattern' [контекст]"
        return 1
    fi

    echo -e "${BLUE}🔍 Поиск '$pattern' в логах (контекст: $context строк):${NC}"
    echo "$(printf '=%.0s' {1..60})"

    for log_file in "$LOGS_DIR"/*.log; do
        if [ -f "$log_file" ] && [ -s "$log_file" ]; then
            local filename=$(basename "$log_file")
            local matches=$(grep -c "$pattern" "$log_file" 2>/dev/null)

            if [ "$matches" -gt 0 ]; then
                echo -e "${GREEN}📄 $filename ($matches совпадений):${NC}"
                grep -C "$context" --color=always "$pattern" "$log_file" | head -20
                echo ""
            fi
        fi
    done
}

# Главная функция
main() {
    case "$1" in
        "interactive" | "i")
            interactive_viewer
            ;;
        "api")
            pretty_logs "$LOGS_DIR/backend-api.log" "${2:-50}"
            ;;
        "api-out")
            pretty_logs "$LOGS_DIR/backend-api-out.log" "${2:-50}"
            ;;
        "api-error")
            pretty_logs "$LOGS_DIR/backend-api-error.log" "${2:-50}"
            ;;
        "errors")
            echo -e "${RED}🚨 Все ошибки:${NC}"
            pretty_logs "$LOGS_DIR/backend-api-error.log" 30
            pretty_logs "$LOGS_DIR/backend-worker-error.log" 30
            ;;
        "stats")
            show_log_stats
            ;;
        "search")
            search_logs "$2" "$3"
            ;;
        "follow")
            echo -e "${BLUE}📡 Отслеживание всех логов API...${NC}"
            echo "Нажмите Ctrl+C для остановки"
            tail -f "$LOGS_DIR/backend-api.log" "$LOGS_DIR/backend-api-out.log" "$LOGS_DIR/backend-api-error.log"
            ;;
        *)
            echo -e "${BLUE}🔍 Log Viewer для Yandex Parser API${NC}"
            echo ""
            echo -e "${GREEN}Доступные команды:${NC}"
            echo "  interactive, i  - Интерактивный режим"
            echo "  api [lines]     - API логи (по умолчанию 50 строк)"
            echo "  api-out [lines] - API stdout"
            echo "  api-error [lines] - API ошибки"
            echo "  errors          - Все ошибки"
            echo "  stats           - Статистика файлов"
            echo "  search 'pattern' [context] - Поиск в логах"
            echo "  follow          - Отслеживание в реальном времени"
            echo ""
            echo -e "${YELLOW}Примеры:${NC}"
            echo "  ./log-viewer.sh interactive"
            echo "  ./log-viewer.sh api-error 100"
            echo "  ./log-viewer.sh search 'TypeError' 5"
            ;;
    esac
}

# Запуск
main "$@"
