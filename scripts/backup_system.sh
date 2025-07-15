#!/bin/bash

# Система бэкапов для TopFlight
# scripts/backup_system.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKUP_DIR="/var/backups/topflight"
DATE=$(date +%Y%m%d_%H%M%S)
LOG_FILE="$PROJECT_ROOT/logs/backup_$DATE.log"

# Создаем директорию бэкапов
sudo mkdir -p "$BACKUP_DIR"

log_backup() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') BACKUP: $1" | tee -a "$LOG_FILE"
}

log_backup "🔄 Starting TopFlight backup..."

# Бэкап базы данных
log_backup "📊 Backing up PostgreSQL database..."
if pg_dump -h localhost -U postgres yandex_parser > "$BACKUP_DIR/database_$DATE.sql"; then
    log_backup "✅ Database backup completed"
    gzip "$BACKUP_DIR/database_$DATE.sql"
    log_backup "📦 Database backup compressed"
else
    log_backup "❌ Database backup failed"
    exit 1
fi

# Бэкап конфигураций
log_backup "⚙️ Backing up configurations..."
CONFIG_BACKUP="$BACKUP_DIR/config_$DATE.tar.gz"
tar -czf "$CONFIG_BACKUP" \
    "$PROJECT_ROOT/backend/.env" \
    "$PROJECT_ROOT/docker-compose.yml" \
    "/etc/systemd/system/xvfb-main.service" \
    "/etc/systemd/system/vnc-cleanup.service" \
    "/etc/nginx/sites-available/topflight" \
    2>/dev/null || true

if [ -f "$CONFIG_BACKUP" ]; then
    log_backup "✅ Configuration backup completed"
else
    log_backup "⚠️ Configuration backup had issues"
fi

# Бэкап логов (последние 7 дней)
log_backup "📋 Backing up recent logs..."
LOGS_BACKUP="$BACKUP_DIR/logs_$DATE.tar.gz"
find "$PROJECT_ROOT/logs" -name "*.log" -mtime -7 -print0 | \
    tar -czf "$LOGS_BACKUP" --null -T - 2>/dev/null || true

if [ -f "$LOGS_BACKUP" ]; then
    log_backup "✅ Logs backup completed"
fi

# Бэкап пользовательских данных (профили, стратегии)
log_backup "👤 Backing up user data..."
USER_DATA_BACKUP="$BACKUP_DIR/userdata_$DATE.sql.gz"
if pg_dump -h localhost -U postgres yandex_parser \
    -t profiles -t user_strategies -t user_domains -t user_keywords \
    | gzip > "$USER_DATA_BACKUP"; then
    log_backup "✅ User data backup completed"
else
    log_backup "❌ User data backup failed"
fi

# Очистка старых бэкапов (старше 30 дней)
log_backup "🧹 Cleaning old backups..."
find "$BACKUP_DIR" -name "*_*.sql.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*_*.tar.gz" -mtime +30 -delete
log_backup "✅ Old backups cleaned"

# Расчет размеров
TOTAL_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)
log_backup "📊 Total backup size: $TOTAL_SIZE"

log_backup "🎉 Backup completed successfully!"
