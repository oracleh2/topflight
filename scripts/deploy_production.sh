#!/bin/bash

# Скрипт развертывания TopFlight в production
# scripts/deploy_production.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
DEPLOY_LOG="$PROJECT_ROOT/logs/deploy_$(date +%Y%m%d_%H%M%S).log"

echo "🚀 TopFlight Production Deployment" | tee "$DEPLOY_LOG"

# Проверка прав
if [ "$(id -u)" = "0" ]; then
    echo "❌ Do not run this script as root!" | tee -a "$DEPLOY_LOG"
    exit 1
fi

if [ "$(whoami)" != "topflight" ]; then
    echo "❌ This script should be run as 'topflight' user!" | tee -a "$DEPLOY_LOG"
    exit 1
fi

# Проверка директории
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "❌ Project directory $PROJECT_ROOT not found!" | tee -a "$DEPLOY_LOG"
    exit 1
fi

cd "$PROJECT_ROOT"

# Создание необходимых директорий
echo "📁 Creating directories..." | tee -a "$DEPLOY_LOG"
mkdir -p logs data/postgres data/redis data/vnc data/vnc_tokens data/prometheus data/grafana
chmod 755 logs data

# Backend setup
echo "🐍 Setting up backend..." | tee -a "$DEPLOY_LOG"
cd backend

# Виртуальное окружение
if [ ! -d "venv" ]; then
    python3.11 -m venv venv
    echo "✅ Virtual environment created" | tee -a "$DEPLOY_LOG"
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
echo "✅ Python dependencies installed" | tee -a "$DEPLOY_LOG"

# Конфигурация
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "⚠️ Created .env file - please edit with your settings!" | tee -a "$DEPLOY_LOG"
fi

# Миграции базы данных
echo "🗄️ Running database migrations..." | tee -a "$DEPLOY_LOG"
alembic upgrade head
echo "✅ Database migrations completed" | tee -a "$DEPLOY_LOG"

# Frontend setup
echo "🎨 Setting up frontend..." | tee -a "$DEPLOY_LOG"
cd ../frontend
npm install
npm run build
echo "✅ Frontend built" | tee -a "$DEPLOY_LOG"

# Установка VNC сервисов
echo "🖥️ Installing VNC services..." | tee -a "$DEPLOY_LOG"
cd "$PROJECT_ROOT"
chmod +x scripts/install_vnc_services.sh
sudo scripts/install_vnc_services.sh

# Docker services
echo "🐳 Starting Docker services..." | tee -a "$DEPLOY_LOG"
docker-compose up -d postgres redis
echo "✅ Docker services started" | tee -a "$DEPLOY_LOG"

# Проверка сервисов
echo "🔍 Checking services..." | tee -a "$DEPLOY_LOG"
sleep 10

# Проверка PostgreSQL
if pg_isready -h localhost -U postgres; then
    echo "✅ PostgreSQL is ready" | tee -a "$DEPLOY_LOG"
else
    echo "❌ PostgreSQL is not ready" | tee -a "$DEPLOY_LOG"
fi

# Проверка Redis
if redis-cli ping >/dev/null 2>&1; then
    echo "✅ Redis is ready" | tee -a "$DEPLOY_LOG"
else
    echo "❌ Redis is not ready" | tee -a "$DEPLOY_LOG"
fi

# Создание администратора
echo "👤 Creating admin user..." | tee -a "$DEPLOY_LOG"
cd "$PROJECT_ROOT/backend"
source venv/bin/activate
python create_admin_user.py

echo "🎉 TopFlight deployment completed!" | tee -a "$DEPLOY_LOG"
echo "" | tee -a "$DEPLOY_LOG"
echo "📋 Next steps:" | tee -a "$DEPLOY_LOG"
echo "1. Configure .env file in backend/" | tee -a "$DEPLOY_LOG"
echo "2. Set up nginx reverse proxy" | tee -a "$DEPLOY_LOG"
echo "3. Configure SSL certificates" | tee -a "$DEPLOY_LOG"
echo "4. Set up monitoring and backups" | tee -a "$DEPLOY_LOG"
echo "5. Test VNC system: scripts/test_vnc_system.sh" | tee -a "$DEPLOY_LOG"
