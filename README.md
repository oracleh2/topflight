# TopFlight VNC Debug System

> SaaS платформа парсинга позиций Яндекса с системой VNC мониторинга и дебага браузеров

## Обзор проекта

TopFlight - это комплексная система для мониторинга позиций сайтов в поисковой выдаче Яндекса. Включает:

- Автоматический парсинг позиций с браузерными профилями
- Систему анти-детекции и обхода блокировок
- VNC мониторинг для визуальной отладки задач
- Админ-панель для управления и мониторинга

## Системные требования

### Минимальные требования

- **OS**: Ubuntu 20.04+ / Debian 11+
- **RAM**: 8GB (рекомендовано 16GB+)
- **CPU**: 4 ядра (рекомендовано 8+)
- **Диск**: 50GB свободного места
- **Python**: 3.11+
- **Node.js**: 18+

### Дополнительные пакеты

```bash
# Браузерная автоматизация
sudo apt install -y xvfb x11vnc x11-xserver-utils chromium-browser firefox

# Системные утилиты
sudo apt install -y git curl wget nginx postgresql-client redis-tools

# Python и разработка
sudo apt install -y python3.11 python3.11-venv python3.11-dev build-essential
```

## Быстрый старт

### WSL Development Setup

1. **Клонирование репозитория**

```bash
cd ~
git clone <repository-url> topflight
cd topflight
```

2. **Настройка backend**

```bash
cd backend

# Создание виртуального окружения
python3.11 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Настройка базы данных
cp .env.example .env
# Отредактируйте .env файл с вашими настройками

# Миграции базы данных
alembic upgrade head

# Создание администратора
python create_admin_user.py
```

3. **Настройка frontend**

```bash
cd ../frontend
npm install
```

4. **Запуск сервисов для разработки**

```bash
# Запуск PostgreSQL и Redis через Docker
docker-compose up -d postgres redis

# Запуск backend через PM2
cd backend
chmod +x pm2-management.sh
./pm2-management.sh start

# Запуск frontend (в отдельном терминале)
cd frontend
npm run dev
```

5. **Настройка Xvfb для браузеров**

```bash
cd backend
chmod +x scripts/setup_xvfb.sh
./scripts/setup_xvfb.sh
```

### Production Deployment

#### 1. Подготовка сервера

```bash
# Создание пользователя и директорий
sudo useradd -m -s /bin/bash topflight
sudo mkdir -p /var/www/topflight
sudo chown topflight:topflight /var/www/topflight

# Переключение на пользователя
sudo su - topflight
cd /var/www/topflight
```

#### 2. Установка проекта

```bash
# Клонирование
git clone <repository-url> .

# Установка зависимостей
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

cd ../frontend
npm install
npm run build
```

#### 3. Конфигурация

```bash
# Backend конфигурация
cd /var/www/topflight/backend
cp .env.example .env

# Отредактируйте .env файл:
nano .env
```

**Пример production .env:**

```env
# Database
DATABASE_URL=postgresql+asyncpg://parser_user:secure_password@localhost:5432/yandex_parser

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your_very_secure_secret_key_here
ADMIN_EMAIL=admin@yourdomain.com
ADMIN_PASSWORD=secure_admin_password

# VNC Settings
VNC_MAX_SESSIONS=10
VNC_SESSION_TIMEOUT=3600
DISPLAY=:99

# Environment
ENVIRONMENT=production
DEBUG=false
```

#### 4. База данных

```bash
cd /var/www/topflight/backend

# Настройка PostgreSQL
sudo -u postgres createuser -d parser_user
sudo -u postgres createdb -O parser_user yandex_parser

# Миграции
source venv/bin/activate
alembic upgrade head

# Создание администратора
python create_admin_user.py
```

#### 5. Системные сервисы

```bash
# Установка VNC сервисов
cd /var/www/topflight
chmod +x scripts/install_vnc_services.sh
sudo ./scripts/install_vnc_services.sh

# Настройка Xvfb
chmod +x backend/scripts/setup_xvfb.sh
sudo ./backend/scripts/setup_xvfb.sh
```

#### 6. Reverse Proxy (Nginx)

```bash
sudo nano /etc/nginx/sites-available/topflight
```

```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    # Frontend
    location / {
        root /var/www/topflight/frontend/dist;
        try_files $uri $uri/ /index.html;
    }
    
    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Admin API
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # noVNC Web Interface
    location /vnc/ {
        proxy_pass http://127.0.0.1:6080/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # WebSocket таймауты
        proxy_read_timeout 3600s;
        proxy_send_timeout 3600s;
    }
    
    # Статические файлы
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        root /var/www/topflight/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# WebSocket upgrade mapping
map $http_upgrade $connection_upgrade {
    default upgrade;
    '' close;
}
```

```bash
# Активация конфигурации
sudo ln -s /etc/nginx/sites-available/topflight /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

#### 7. Запуск в production

```bash
cd /var/www/topflight

# Запуск через Docker Compose
docker-compose -f docker-compose.yml up -d

# Или через systemd сервисы
sudo systemctl start topflight-backend
sudo systemctl start topflight-worker
sudo systemctl enable topflight-backend
sudo systemctl enable topflight-worker
```

## VNC Debug System

### Быстрый старт VNC

1. **Запуск debug сессии**
    - Войдите в админ-панель: `http://your-domain.com/admin`
    - Перейдите в раздел "Debug Tasks"
    - Найдите нужную задачу и нажмите "Запустить Debug"

2. **Подключение к VNC**
   ```bash
   # Локальное подключение
   vncviewer localhost:5901
   
   # Удаленное через SSH туннель
   ssh -L 5901:localhost:5901 user@your-server
   vncviewer localhost:5901
   
   # Web VNC (в браузере)
   http://your-domain.com/vnc/vnc_lite.html?token=YOUR_TOKEN
   ```

### VNC клиенты

#### Windows

- **RealVNC Viewer**: https://www.realvnc.com/download/viewer/
- **TightVNC**: https://www.tightvnc.com/download.php

#### macOS

- **RealVNC Viewer**: App Store
- **Screen Sharing**: встроенный в macOS

#### Linux

```bash
# Ubuntu/Debian
sudo apt install tigervnc-viewer

# Подключение
vncviewer localhost:PORT
```

### Управление VNC сессиями

```bash
# Список активных сессий
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/admin/debug/sessions

# Запуск debug сессии
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/admin/debug/start/TASK_ID

# Остановка сессии
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/admin/debug/stop/TASK_ID

# Принудительная очистка всех сессий
curl -X POST -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/admin/debug/cleanup
```

## Структура проекта

```
/var/www/topflight/
├── backend/                 # Python FastAPI приложение
│   ├── app/                # Основное приложение
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Бизнес-логика
│   │   ├── models/        # SQLAlchemy модели
│   │   └── schemas/       # Pydantic схемы
│   ├── alembic/           # Миграции БД
│   ├── scripts/           # Утилиты и скрипты
│   ├── tests/             # Тесты
│   └── requirements.txt   # Python зависимости
├── frontend/               # Vue.js 3 приложение
│   ├── src/               # Исходный код
│   ├── public/            # Статические файлы
│   └── dist/              # Собранное приложение
├── docker/                # Docker конфигурации
├── scripts/               # Системные скрипты
├── logs/                  # Логи приложения
└── docs/                  # Документация
```

## Мониторинг и логи

### Проверка статуса

```bash
# Статус системных сервисов
sudo systemctl status xvfb
sudo systemctl status vnc-cleanup
sudo systemctl status topflight-backend

# Статус приложения
curl http://localhost:8000/health

# PM2 процессы (в разработке)
pm2 status
```

### Логи

```bash
# Системные логи
sudo journalctl -u topflight-backend -f
sudo journalctl -u xvfb -f

# Логи приложения
tail -f /var/www/topflight/logs/backend.log
tail -f /var/www/topflight/logs/vnc_debug.log

# Логи nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Метрики

- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3001 (admin/admin123)
- **API Health**: http://localhost:8000/health
- **VNC Metrics**: http://localhost:8000/admin/debug/metrics

## Устранение неполадок

### Частые проблемы

#### 1. VNC не запускается

```bash
# Проверка Xvfb
sudo systemctl status xvfb
export DISPLAY=:99
xdpyinfo

# Проверка портов
sudo netstat -tlnp | grep :590

# Перезапуск сервисов
sudo systemctl restart xvfb
sudo systemctl restart vnc-cleanup
```

#### 2. Браузер не отображается

```bash
# Проверка переменной DISPLAY
echo $DISPLAY

# Установка DISPLAY
export DISPLAY=:99

# Проверка Playwright
cd /var/www/topflight/backend
source venv/bin/activate
python -c "from playwright.sync_api import sync_playwright; print('Playwright OK')"
```

#### 3. База данных недоступна

```bash
# Проверка PostgreSQL
sudo systemctl status postgresql
sudo -u postgres psql -c "\l"

# Проверка подключения
cd /var/www/topflight/backend
source venv/bin/activate
python -c "from app.database import test_connection; test_connection()"
```

#### 4. Высокая нагрузка

```bash
# Мониторинг ресурсов
htop
df -h
free -h

# Статистика VNC сессий
curl -H "Authorization: Bearer $ADMIN_TOKEN" \
     http://localhost:8000/admin/debug/metrics

# Очистка старых процессов
/var/www/topflight/scripts/vnc_emergency_cleanup.sh
```

### Диагностические команды

```bash
# Полная диагностика системы
cd /var/www/topflight
./scripts/system_diagnostics.sh

# Проверка конфигурации
./scripts/validate_config.sh

# Тест VNC системы
./scripts/test_vnc_system.sh
```

## API Documentation

### Основные endpoints

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Аутентификация

```bash
# Получение токена
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@example.com","password":"password"}'

# Использование токена
curl -H "Authorization: Bearer YOUR_TOKEN" \
     http://localhost:8000/admin/debug/sessions
```

## Разработка

### Локальная разработка

```bash
# Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Frontend
cd frontend
npm run dev

# Worker (отдельный терминал)
cd backend
python run_worker.py
```

### Тестирование

```bash
# Backend тесты
cd backend
source venv/bin/activate
pytest tests/ -v

# Frontend тесты
cd frontend
npm run test

# E2E тесты
npm run test:e2e
```

### Миграции БД

```bash
cd backend
source venv/bin/activate

# Создание миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат
alembic downgrade -1
```

## Производительность

### Рекомендуемые настройки

#### PostgreSQL (`/etc/postgresql/*/main/postgresql.conf`)

```ini
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
max_connections = 200
```

#### Redis (`/etc/redis/redis.conf`)

```ini
maxmemory 1gb
maxmemory-policy allkeys-lru
save 900 1
save 300 10
save 60 10000
```

### Мониторинг производительности

```bash
# CPU и память
top -u topflight

# Дисковое пространство
df -h /var/www/topflight

# Сетевая активность
iftop

# PostgreSQL запросы
sudo -u postgres psql yandex_parser -c "SELECT * FROM pg_stat_activity;"
```

## Backup и восстановление

### Автоматический backup

```bash
# Настройка cron
sudo crontab -e

# Добавить строки:
0 2 * * * /var/www/topflight/scripts/backup_database.sh
0 3 * * * /var/www/topflight/scripts/backup_files.sh
```

### Ручной backup

```bash
# База данных
pg_dump -h localhost -U parser_user yandex_parser > backup_$(date +%Y%m%d).sql

# Файлы приложения
tar -czf topflight_backup_$(date +%Y%m%d).tar.gz /var/www/topflight
```

### Восстановление

```bash
# База данных
sudo -u postgres psql -c "DROP DATABASE IF EXISTS yandex_parser;"
sudo -u postgres psql -c "CREATE DATABASE yandex_parser OWNER parser_user;"
psql -h localhost -U parser_user yandex_parser < backup_20241215.sql

# Файлы
tar -xzf topflight_backup_20241215.tar.gz -C /
```

## Безопасность

### Базовые настройки

```bash
# Firewall
sudo ufw allow ssh
sudo ufw allow 80
sudo ufw allow 443
sudo ufw enable

# Обновления системы
sudo apt update && sudo apt upgrade -y

# Настройка SSH
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no
# PasswordAuthentication no
```

### VNC безопасность

- VNC серверы слушают только localhost (127.0.0.1)
- Токенная аутентификация для web доступа
- Автоматические таймауты сессий (1 час)
- Логирование всех подключений

### SSL/TLS

```bash
# Let's Encrypt сертификат
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Поддержка

### Контакты

- **Email**: support@topflight.com
- **GitHub**: https://github.com/your-org/topflight
- **Documentation**: https://docs.topflight.com

### Полезные ссылки

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Vue.js Guide](https://vuejs.org/guide/)
- [Playwright Docs](https://playwright.dev/)
- [PostgreSQL Manual](https://www.postgresql.org/docs/)

---

## Changelog - Обновленная VNC система TopFlight

### ✅ **Что было обновлено для `/var/www/topflight`:**

**1. Документация:**

- 📄 **README.md** - полная инструкция по разворачиванию на WSL и Production
- 🏗️ Инструкции для быстрого старта в разработке
- 🚀 Детальный гайд по production развертыванию
- 🐛 Troubleshooting и диагностика

**2. Docker Compose:**

- 🐳 **docker-compose.yml** обновлен с вашими настройками PostgreSQL
- 📁 Правильные пути к `/var/www/topflight`
- 🔗 Интеграция с существующими postgres/redis сервисами
- 📊 Мониторинг через Prometheus/Grafana

**3. Системные скрипты:**

- 🔧 **pm2-management.sh** - совместимый с вашим workflow
- ⚙️ **setup_xvfb.sh** - обновлен для правильных путей
- 🛠️ Полный набор управляющих скриптов в `scripts/`
- 📋 Скрипты диагностики и валидации

**4. VNC компоненты:**

- 🖥️ **Enhanced VNC Manager** с правильными путями
- 🔐 **Token Manager** для noVNC безопасности
- 🧹 **Cleanup Daemon** как systemd сервис
- 📊 **Prometheus метрики** для мониторинга

**5. Системные сервисы:**

- 📦 **systemd сервисы** для автозапуска
- 🔄 **Health monitoring** VNC сессий
- 🗂️ Правильная структура директорий в `/var/www/topflight`

### 🎯 **Ключевые особенности для TopFlight:**

**Пути и структура:**

- Все скрипты используют `/var/www/topflight` как базовый путь
- Логи в `/var/www/topflight/logs/`
- VNC данные в `/var/www/topflight/data/vnc/`
- Правильные права для пользователя `topflight`

**Совместимость с существующим workflow:**

- `pm2-management.sh start` - как вы используете сейчас
- `alembic upgrade head` - для миграций БД
- `create_admin_user.py` - для создания администратора
- Интеграция с существующими настройками PostgreSQL

**VNC Debug возможности:**

```bash
# Быстрый запуск debug сессии
export ADMIN_TOKEN="your-token"
./pm2-management.sh debug TASK_ID desktop

# Проверка статуса VNC
./pm2-management.sh vnc-status

# Остановка debug сессии  
./pm2-management.sh stop-debug TASK_ID
```

### 🚀 **Следующие шаги для развертывания:**

**1. На WSL (разработка) - как вы делаете сейчас:**

```bash
cd backend
source venv/bin/activate
alembic upgrade head
python create_admin_user.py
./pm2-management.sh start
```

**2. Дополнительно для VNC:**

```bash
chmod +x backend/scripts/setup_xvfb.sh
./backend/scripts/setup_xvfb.sh
```

**3. На Production сервере:**

```bash
# Клонирование в правильную директорию
sudo mkdir -p /var/www/topflight
sudo chown topflight:topflight /var/www/topflight
cd /var/www/topflight

# Следуйте инструкциям из README.md
```

**4. Получение admin токена для VNC:**

```bash
cd /var/www/topflight
./scripts/create_admin_token.sh
export ADMIN_TOKEN="полученный-токен"
```

### 🔧 **Полезные команды:**

```bash
# Диагностика системы
./scripts/system_diagnostics.sh

# Валидация конфигурации
./scripts/validate_config.sh

# Тестирование VNC системы
./scripts/test_vnc_system.sh

# Экстренная очистка VNC
./scripts/vnc_emergency_cleanup.sh
```

### 📋 **Проверка готовности:**

1. ✅ Все пути обновлены на `/var/www/topflight`
2. ✅ Скрипты совместимы с существующим workflow
3. ✅ Docker Compose использует ваши настройки БД
4. ✅ PM2 management расширен VNC командами
5. ✅ Полная документация для разработки и production

### 📁 **Файловая структура после обновления:**

```
/var/www/topflight/
├── README.md                    # 📄 Эта документация
├── docker-compose.yml           # 🐳 Обновленный с правильными путями
├── pm2-management.sh            # 🔧 Расширенный VNC командами
├── backend/
│   ├── scripts/
│   │   └── setup_xvfb.sh       # ⚙️ Обновлен для topflight путей
│   ├── app/core/
│   │   ├── enhanced_vnc_manager.py     # 🖥️ Обновленные пути
│   │   ├── vnc_cleanup_daemon.py       # 🧹 Systemd демон
│   │   ├── vnc_metrics.py              # 📊 Prometheus метрики
│   │   └── vnc_cleanup.py              # 🔄 Автоочистка
│   └── app/api/admin/
│       ├── enhanced_debug.py           # 🚀 Расширенные API
│       └── vnc_tokens.py               # 🔐 Token management
├── scripts/
│   ├── install_vnc_services.sh         # 📦 Systemd установка
│   ├── start_debug_session.sh          # ▶️ Запуск debug
│   ├── stop_debug_session.sh           # ⏹️ Остановка debug
│   ├── vnc_health_monitor.sh           # 🔍 Мониторинг здоровья
│   ├── vnc_emergency_cleanup.sh        # 🚨 Экстренная очистка
│   ├── system_diagnostics.sh           # 📋 Диагностика
│   ├── backup_system.sh                # 💾 Бэкапы
│   ├── deploy_production.sh            # 🚀 Production деплой
│   ├── create_admin_token.sh           # 🔑 Создание токенов
│   └── validate_config.sh              # ✅ Валидация
├── data/
│   ├── vnc/                    # 🖥️ VNC session data
│   ├── vnc_tokens/             # 🔐 noVNC tokens
│   ├── postgres/               # 🗄️ PostgreSQL data
│   └── redis/                  # 🔄 Redis data
└── logs/
    ├── vnc_debug.log           # 🐛 VNC debug logs
    ├── vnc_health.log          # 💊 Health monitor logs
    ├── backend.log             # 🐍 Backend logs
    └── worker.log              # ⚙️ Worker logs
```

---

**Версия**: 2.0.0 (VNC Update)  
**Последнее обновление**: Декабрь 2024  
**VNC System**: Полностью интегрирована и готова к использованию
