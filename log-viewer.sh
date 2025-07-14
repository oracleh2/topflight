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
        if [ -f "$file_with_suffix" ] && [ -s "$file_with_suffix" ]; then
            echo "$file_with_suffix"
            return 0
        fi
    done

    # Если ничего не найдено, возвращаем базовое имя
    echo "$LOGS_DIR/$base_name"
    return 1
}

# Функция красивого вывода логов с подсветкой
pretty_logs() {
    local base_file="$1"
    local lines="${2:-50}"

    # Находим актуальный файл
    local actual_file=$(find_log_file "$base_file")

    if [ ! -f "$actual_file" ]; then
        echo -e "${RED}❌ Файл логов не найден: $actual_file${NC}"
        echo -e "${YELLOW}💡 Проверьте, что PM2 процессы запущены${NC}"
        return 1
    fi

    if [ ! -s "$actual_file" ]; then
        echo -e "${YELLOW}⚠️ Файл логов пустой: $(basename "$actual_file")${NC}"
        return 1
    fi

    echo -e "${BLUE}📋 Последние $lines строк из $(basename "$actual_file"):${NC}"
    echo -e "${PURPLE}$actual_file${NC}"
    echo "$(printf '=%.0s' {1..80})"

    # Подсвечиваем разные типы сообщений
    tail -"$lines" "$actual_file" | while IFS= read -r line; do
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

# Функция для получения всех файлов определенного типа (включая ротированные)
get_all_log_files() {
    local base_name="$1"
    local files=()

    # Добавляем базовый файл если он существует
    if [ -f "$LOGS_DIR/$base_name" ]; then
        files+=("$LOGS_DIR/$base_name")
    fi

    # Добавляем ротированные файлы
    for i in {0..9}; do
        local file_with_suffix="$LOGS_DIR/${base_name%%.log}-${i}.log"
        if [ -f "$file_with_suffix" ]; then
            files+=("$file_with_suffix")
        fi
    done

    printf '%s\n' "${files[@]}"
}

# Функция интерактивного просмотра логов
interactive_viewer() {
    while true; do
        clear
        echo -e "${BLUE}🔍 Интерактивный просмотрщик логов (Backend)${NC}"
        echo "$(printf '=%.0s' {1..50})"
        echo ""
        echo -e "${GREEN}Доступные логи:${NC}"
        echo "1) API общие логи (backend-api.log)"
        echo "2) API stdout (backend-api-out.log)"
        echo "3) API ошибки (backend-api-error.log)"
        echo "4) Worker логи (backend-worker.log)"
        echo "5) Worker stdout (backend-worker-out.log)"
        echo "6) Worker ошибки (backend-worker-error.log)"
        echo "7) Monitor логи (backend-monitor.log)"
        echo "8) Monitor stdout (backend-monitor-out.log)"
        echo "9) Monitor ошибки (backend-monitor-error.log)"
        echo "10) Все ошибки (error логи)"
        echo "11) Статистика файлов логов"
        echo "12) Показать все доступные файлы"
        echo "13) Очистить экран"
        echo "0) Выход"
        echo ""

        read -p "Выберите опцию (0-13): " choice

        case $choice in
            1)
                pretty_logs "backend-api.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            2)
                pretty_logs "backend-api-out.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            3)
                pretty_logs "backend-api-error.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            4)
                pretty_logs "backend-worker.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            5)
                pretty_logs "backend-worker-out.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            6)
                pretty_logs "backend-worker-error.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            7)
                pretty_logs "backend-monitor.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            8)
                pretty_logs "backend-monitor-out.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            9)
                pretty_logs "backend-monitor-error.log" 100
                read -p "Нажмите Enter для продолжения..."
                ;;
            10)
                echo -e "${RED}🚨 Все ошибки Backend:${NC}"
                echo ""
                echo -e "${YELLOW}API Ошибки:${NC}"
                pretty_logs "backend-api-error.log" 20
                echo -e "${YELLOW}Worker Ошибки:${NC}"
                pretty_logs "backend-worker-error.log" 20
                echo -e "${YELLOW}Monitor Ошибки:${NC}"
                pretty_logs "backend-monitor-error.log" 20
                read -p "Нажмите Enter для продолжения..."
                ;;
            11)
                show_log_stats
                read -p "Нажмите Enter для продолжения..."
                ;;
            12)
                list_all_files
                read -p "Нажмите Enter для продолжения..."
                ;;
            13)
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

# Функция показа всех доступных файлов
list_all_files() {
    echo -e "${BLUE}📁 Все доступные файлы логов:${NC}"
    echo "$(printf '=%.0s' {1..60})"

    for log_file in "$LOGS_DIR"/*.log; do
        if [ -f "$log_file" ]; then
            local filename=$(basename "$log_file")
            local size=$(du -h "$log_file" | cut -f1)
            local lines=$(wc -l < "$log_file")
            local modified=$(stat -c %y "$log_file" | cut -d' ' -f1,2 | cut -d'.' -f1)

            if [[ "$filename" == backend-* ]]; then
                echo -e "${GREEN}📄 $filename${NC}"
            else
                echo -e "${CYAN}📄 $filename${NC}"
            fi
            echo "   Размер: $size, Строк: $lines, Изменен: $modified"
            echo ""
        fi
    done
}

# Функция показа статистики логов (только backend)
show_log_stats() {
    echo -e "${BLUE}📊 Статистика файлов логов Backend:${NC}"
    echo "$(printf '=%.0s' {1..60})"

    # Группируем файлы по типу
    declare -A log_groups

    for log_file in "$LOGS_DIR"/backend-*.log; do
        if [ -f "$log_file" ]; then
            local filename=$(basename "$log_file")
            local base_name="${filename%-*}"
            if [[ "$filename" == *-[0-9].log ]]; then
                base_name="${filename%-[0-9].log}"
            fi

            if [ -z "${log_groups[$base_name]}" ]; then
                log_groups[$base_name]="$log_file"
            else
                log_groups[$base_name]="${log_groups[$base_name]} $log_file"
            fi
        fi
    done

    for base_name in "${!log_groups[@]}"; do
        echo -e "${GREEN}📄 $base_name группа:${NC}"
        for file in ${log_groups[$base_name]}; do
            local filename=$(basename "$file")
            local size=$(du -h "$file" | cut -f1)
            local lines=$(wc -l < "$file")
            local modified=$(stat -c %y "$file" | cut -d' ' -f1,2 | cut -d'.' -f1)
            echo "   $filename: $size, $lines строк, $modified"
        done
        echo ""
    done
}

# Функция поиска в логах (только backend)
search_logs() {
    local pattern="$1"
    local context="${2:-3}"

    if [ -z "$pattern" ]; then
        echo -e "${RED}❌ Укажите паттерн для поиска${NC}"
        echo "Использование: $0 search 'error pattern' [контекст]"
        return 1
    fi

    echo -e "${BLUE}🔍 Поиск '$pattern' в логах Backend (контекст: $context строк):${NC}"
    echo "$(printf '=%.0s' {1..60})"

    for log_file in "$LOGS_DIR"/backend-*.log; do
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

# Функция follow с поддержкой ротированных файлов
follow_logs() {
    local log_type="$1"
    local files=()

    case "$log_type" in
        "api")
            files=($(get_all_log_files "backend-api.log"))
            ;;
        "api-out")
            files=($(get_all_log_files "backend-api-out.log"))
            ;;
        "api-error")
            files=($(get_all_log_files "backend-api-error.log"))
            ;;
        "worker")
            files=($(get_all_log_files "backend-worker.log"))
            ;;
        "worker-error")
            files=($(get_all_log_files "backend-worker-error.log"))
            ;;
        "monitor")
            files=($(get_all_log_files "backend-monitor.log"))
            ;;
        "monitor-error")
            files=($(get_all_log_files "backend-monitor-error.log"))
            ;;
        "all")
            files=($(get_all_log_files "backend-api.log" && get_all_log_files "backend-api-out.log" && get_all_log_files "backend-api-error.log"))
            ;;
        "errors")
            files=($(get_all_log_files "backend-api-error.log" && get_all_log_files "backend-worker-error.log" && get_all_log_files "backend-monitor-error.log"))
            ;;
        *)
            echo -e "${RED}❌ Неизвестный тип лога: $log_type${NC}"
            return 1
            ;;
    esac

    if [ ${#files[@]} -eq 0 ]; then
        echo -e "${RED}❌ Не найдено файлов для отслеживания${NC}"
        return 1
    fi

    echo -e "${BLUE}📡 Отслеживание логов: ${files[*]}${NC}"
    echo "Нажмите Ctrl+C для остановки"
    tail -f "${files[@]}"
}

# Главная функция
main() {
    case "$1" in
        "interactive" | "i")
            interactive_viewer
            ;;
        "api")
            pretty_logs "backend-api.log" "${2:-50}"
            ;;
        "api-out")
            pretty_logs "backend-api-out.log" "${2:-50}"
            ;;
        "api-error")
            pretty_logs "backend-api-error.log" "${2:-50}"
            ;;
        "worker")
            pretty_logs "backend-worker.log" "${2:-50}"
            ;;
        "worker-out")
            pretty_logs "backend-worker-out.log" "${2:-50}"
            ;;
        "worker-error")
            pretty_logs "backend-worker-error.log" "${2:-50}"
            ;;
        "monitor")
            pretty_logs "backend-monitor.log" "${2:-50}"
            ;;
        "monitor-out")
            pretty_logs "backend-monitor-out.log" "${2:-50}"
            ;;
        "monitor-error")
            pretty_logs "backend-monitor-error.log" "${2:-50}"
            ;;
        "errors")
            echo -e "${RED}🚨 Все ошибки Backend:${NC}"
            pretty_logs "backend-api-error.log" 30
            pretty_logs "backend-worker-error.log" 30
            pretty_logs "backend-monitor-error.log" 30
            ;;
        "stats")
            show_log_stats
            ;;
        "list")
            list_all_files
            ;;
        "search")
            search_logs "$2" "$3"
            ;;
        "follow")
            follow_logs "${2:-api}"
            ;;
        "follow-errors")
            follow_logs "errors"
            ;;
        "follow-all")
            follow_logs "all"
            ;;
        *)
            echo -e "${BLUE}🔍 Backend Log Viewer для Yandex Parser API${NC}"
            echo ""
            echo -e "${GREEN}Доступные команды:${NC}"
            echo "  interactive, i  - Интерактивный режим"
            echo "  api [lines]     - API логи (по умолчанию 50 строк)"
            echo "  api-out [lines] - API stdout"
            echo "  api-error [lines] - API ошибки"
            echo "  worker [lines]  - Worker логи"
            echo "  worker-out [lines] - Worker stdout"
            echo "  worker-error [lines] - Worker ошибки"
            echo "  monitor [lines] - Monitor логи"
            echo "  monitor-out [lines] - Monitor stdout"
            echo "  monitor-error [lines] - Monitor ошибки"
            echo "  errors          - Все ошибки Backend"
            echo "  stats           - Статистика файлов"
            echo "  list            - Список всех файлов"
            echo "  search 'pattern' [context] - Поиск в логах"
            echo "  follow [type]   - Отслеживание логов в реальном времени"
            echo "  follow-errors   - Отслеживание только error логов"
            echo "  follow-all      - Отслеживание всех Backend логов"
            echo ""
            echo -e "${YELLOW}Примеры:${NC}"
            echo "  ./log-viewer.sh interactive"
            echo "  ./log-viewer.sh api-error 100"
            echo "  ./log-viewer.sh search 'TypeError' 5"
            echo "  ./log-viewer.sh follow api-error"
            echo "  ./log-viewer.sh list"
            ;;
    esac
}

# Запуск
main "$@"
