#!/bin/bash

# Восстановление системы TopFlight из бэкапа
# scripts/restore_system.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKUP_DIR="/var/backups/topflight"
RESTORE_DATE=${1:-}

if [ -z "$RESTORE_DATE" ]; then
    echo "Usage: $0 BACKUP_DATE"
    echo "Available backups:"
    ls -la "$BACKUP_DIR"/database_*.sql.gz | awk '{print $9}' | sed 's/.*database_\(.*\)\.sql\.gz/\1/'
    exit 1
fi

echo "🔄 Restoring TopFlight from backup date: $RESTORE_DATE"
echo "⚠️ This will overwrite current data. Continue? (y/N)"
read -r confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Restore cancelled."
    exit 0
fi

# Остановка сервисов
echo "🛑 Stopping services..."
sudo systemctl stop vnc-cleanup
sudo systemctl stop vnc-health-monitor
docker-compose down || true

# Восстановление базы данных
echo "📊 Restoring database..."
DATABASE_BACKUP="$BACKUP_DIR/database_$RESTORE_DATE.sql.gz"
if [ -f "$DATABASE_BACKUP" ]; then
    # Создаем резервную копию текущей БД
    pg_dump -h localhost -U postgres yandex_parser > "/tmp/current_database_$(date +%Y%m%d_%H%M%S).sql"

    # Восстанавливаем из бэкапа
    sudo -u postgres dropdb yandex_parser || true
    sudo -u postgres createdb yandex_parser
    gunzip -c "$DATABASE_BACKUP" | psql -h localhost -U postgres yandex_parser
    echo "✅ Database restored"
else
    echo "❌ Database backup not found: $DATABASE_BACKUP"
    exit 1
fi

# Восстановление конфигураций
echo "⚙️ Restoring configurations..."
CONFIG_BACKUP="$BACKUP_DIR/config_$RESTORE_DATE.tar.gz"
if [ -f "$CONFIG_BACKUP" ]; then
    tar -xzf "$CONFIG_BACKUP" -C / 2>/dev/null || true
    echo "✅ Configurations restored"
fi

# Перезапуск сервисов
echo "🔄 Starting services..."
sudo systemctl daemon-reload
sudo systemctl start xvfb-main
docker-compose up -d
sudo systemctl start vnc-cleanup
sudo systemctl start vnc-health-monitor

echo "🎉 System restoration completed!"
echo "Please verify all services are running correctly."
