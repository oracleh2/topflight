#!/bin/bash

# Имя выходного файла
OUTPUT_FILE="export.txt"

# Очищаем выходной файл перед началом
> "$OUTPUT_FILE"

# Функция для обработки файлов
process_file() {
    local file="$1"
    # Получаем относительный путь к файлу
    local relative_path="${file#./}"

    # Добавляем путь к файлу в выходной файл
    echo "=== $relative_path ===" >> "$OUTPUT_FILE"
    # Добавляем содержимое файла
    cat "$file" >> "$OUTPUT_FILE"
    # Добавляем пустую строку для разделения
    echo -e "\n" >> "$OUTPUT_FILE"
}

# Экспортируем функцию, чтобы она была доступна в find -exec
export -f process_file
export OUTPUT_FILE

# Ищем и обрабатываем все нужные файлы, исключая каталог venv
find . -type f \( -name "*.py" -o -name "*.txt" -o -name "*.ini" -o -name "*.yml" -o -name ".env*" -o -name "*.vue" -o -name "*.ts" -o -name "*.css"\) \
    -not -path "./venv/*" \
    -not -path "*/venv/*" \
    -not -path "./.venv/*" \
    -not -path "*/.venv/*" \
    -not -path "./export.txt" \
    -not -path "./node_modules/*" \
    -not -path "*/node_modules/*" \
    -exec bash -c 'process_file "$0"' {} \;

echo "Экспорт завершен. Результат сохранён в $OUTPUT_FILE"