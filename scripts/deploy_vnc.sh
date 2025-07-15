#!/bin/bash

# Скрипт развертывания VNC системы
# scripts/deploy_vnc.sh

set -euo pipefail

echo "Deploying VNC Debug System..."

# Проверяем Docker и Docker Compose
if ! command -v docker &> /dev/null; then
    echo "ERROR: Docker is not installed"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "ERROR: Docker Compose is not installed"
    exit 1
fi

# Создаем необходимые директории
mkdir -p logs docker/nginx/ssl docker/grafana/dashboards

# Устанавливаем переменные окружения
export SECRET_KEY=${SECRET_KEY:-$(openssl rand -hex 32)}
export ADMIN_EMAIL=${ADMIN_EMAIL:-admin@example.com}
export ADMIN_PASSWORD=${ADMIN_PASSWORD:-admin123}

# Собираем и запускаем контейнеры
echo "Building containers..."
docker-compose build

echo "Starting services..."
docker-compose up -d

# Ждем запуска всех сервисов
echo "Waiting for services to start..."
sleep 30

# Проверяем статус сервисов
echo "Checking service status..."
docker-compose ps

# Проверяем доступность endpoints
echo "Testing endpoints..."
curl -f http://localhost:8000/health || echo "Backend health check failed"
curl -f http://localhost:6080/ || echo "noVNC web interface failed"
curl -f http://localhost:3000/ || echo "Frontend failed"

echo "VNC Debug System deployed successfully!"
echo ""
echo "Access URLs:"
echo "  Frontend: http://localhost:3000"
echo "  Backend API: http://localhost:8000"
echo "  noVNC Web: http://localhost:6080"
echo "  Grafana: http://localhost:3001"
echo "  Prometheus: http://localhost:9090"
echo ""
echo "Default credentials:"
echo "  Admin: $ADMIN_EMAIL / $ADMIN_PASSWORD"
echo "  Grafana: admin / admin123"
