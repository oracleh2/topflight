#!/bin/bash

# Setup Xvfb for TopFlight project
# backend/scripts/setup_xvfb.sh - Обновленный для TopFlight

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
LOGS_DIR="$PROJECT_ROOT/logs"

echo "🚀 Setting up Xvfb for TopFlight browser automation..."

# Функция для проверки установки пакета
check_package() {
    dpkg -l | grep -q "^ii  $1 "
}

# Функция логирования
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') SETUP: $1" | tee -a "$LOGS_DIR/xvfb_setup.log"
}

# Создаем директории
mkdir -p "$LOGS_DIR"

log "Starting Xvfb setup for TopFlight"

# Список необходимых пакетов
REQUIRED_PACKAGES=(
    "xvfb"
    "x11vnc"
    "x11-xserver-utils"
    "x11-utils"
    "xfonts-100dpi"
    "xfonts-75dpi"
    "xfonts-scalable"
    "xfonts-cyrillic"
    "imagemagick"
    "netcat-openbsd"
)

# Проверка каких пакетов не хватает
MISSING_PACKAGES=()
log "Checking installed packages..."

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! check_package "$package"; then
        MISSING_PACKAGES+=("$package")
        log "Missing: $package"
    else
        log "Found: $package"
    fi
done

# Установка только недостающих пакетов
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    log "Installing missing packages: ${MISSING_PACKAGES[*]}"
    log "Updating package list..."
    sudo apt-get update

    log "Installing packages..."
    sudo apt-get install -y "${MISSING_PACKAGES[@]}"

    if [ $? -eq 0 ]; then
        log "All packages installed successfully!"
    else
        log "Failed to install some packages"
        exit 1
    fi
else
    log "All required packages are already installed!"
fi

# Создание пользователя topflight если не существует
if ! id "topflight" &>/dev/null; then
    log "Creating topflight user..."
    sudo useradd -m -s /bin/bash topflight
    sudo usermod -aG sudo topflight
    log "User topflight created"
else
    log "User topflight already exists"
fi

# Настройка прав доступа
log "Setting up permissions..."
sudo chown -R topflight:topflight "$PROJECT_ROOT" 2>/dev/null || true
sudo mkdir -p "$PROJECT_ROOT/data/vnc" "$PROJECT_ROOT/data/vnc_tokens"
sudo chown -R topflight:topflight "$PROJECT_ROOT/data" 2>/dev/null || true

# Проверка существования systemd сервиса для основного Xvfb
SERVICE_NAME="xvfb-main"
if [ ! -f "/etc/systemd/system/$SERVICE_NAME.service" ]; then
    log "Creating systemd service: $SERVICE_NAME"
    sudo tee /etc/systemd/system/$SERVICE_NAME.service > /dev/null <<EOF
[Unit]
Description=Xvfb Main Display for TopFlight Browser Profiles
After=network.target
Wants=network.target

[Service]
Type=simple
User=topflight
Group=topflight
Environment=DISPLAY=:99
Environment=PROJECT_ROOT=$PROJECT_ROOT
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac -nolisten tcp +extension GLX +extension RANDR -dpi 96
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Ресурсы и лимиты
MemoryLimit=512M
CPUQuota=20%

# Безопасность
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=$PROJECT_ROOT /tmp

[Install]
WantedBy=multi-user.target
EOF
    log "Systemd service created: $SERVICE_NAME"
else
    log "Systemd service already exists: $SERVICE_NAME"
fi

# Запуск и включение сервиса
log "Starting Xvfb service..."
sudo systemctl daemon-reload
sudo systemctl enable $SERVICE_NAME

# Проверка статуса сервиса
if sudo systemctl is-active --quiet $SERVICE_NAME; then
    log "Xvfb service is already running!"
else
    log "Starting Xvfb service..."
    sudo systemctl start $SERVICE_NAME
    sleep 3

    if sudo systemctl is-active --quiet $SERVICE_NAME; then
        log "Xvfb service started successfully!"
    else
        log "Failed to start Xvfb service"
        sudo systemctl status $SERVICE_NAME --no-pager
        exit 1
    fi
fi

# Проверка статуса
log "Checking Xvfb status..."
sudo systemctl status $SERVICE_NAME --no-pager || true

# Установка переменной окружения для пользователя topflight
TOPFLIGHT_BASHRC="/home/topflight/.bashrc"
if [ -f "$TOPFLIGHT_BASHRC" ]; then
    if ! grep -q "export DISPLAY=:99" "$TOPFLIGHT_BASHRC"; then
        log "Setting up environment variable for topflight user..."
        echo "export DISPLAY=:99" | sudo tee -a "$TOPFLIGHT_BASHRC" >/dev/null
        echo "export PROJECT_ROOT=$PROJECT_ROOT" | sudo tee -a "$TOPFLIGHT_BASHRC" >/dev/null
        log "Environment variables added to topflight .bashrc"
    else
        log "Environment variables already set in topflight .bashrc"
    fi
fi

# Установка переменной для текущего пользователя
if ! grep -q "export DISPLAY=:99" ~/.bashrc 2>/dev/null; then
    log "Setting up environment variable for current user..."
    echo "export DISPLAY=:99" >> ~/.bashrc
    echo "export PROJECT_ROOT=$PROJECT_ROOT" >> ~/.bashrc
    log "Environment variables added to current user .bashrc"
else
    log "Environment variables already set in current user .bashrc"
fi

# Проверка работы
log "Testing Xvfb..."
export DISPLAY=:99
if command -v xdpyinfo >/dev/null 2>&1; then
    if xdpyinfo >/dev/null 2>&1; then
        log "Xvfb is working correctly!"
        DISPLAY_INFO=$(xdpyinfo | grep "dimensions" | head -1)
        log "Display info: $DISPLAY_INFO"
    else
        log "Xvfb test failed - display not accessible"
        exit 1
    fi
else
    log "xdpyinfo not found, but Xvfb should be working"
fi

# Проверка VNC утилит
log "Testing VNC utilities..."
if command -v x11vnc >/dev/null 2>&1; then
    log "x11vnc is available"
else
    log "x11vnc not found!"
    exit 1
fi

# Создание тестового скрипта
TEST_SCRIPT="$PROJECT_ROOT/scripts/test_display.sh"
mkdir -p "$(dirname "$TEST_SCRIPT")"
cat > "$TEST_SCRIPT" << 'EOF'
#!/bin/bash
# Test script for TopFlight display

export DISPLAY=:99
export PROJECT_ROOT="/var/www/topflight"

echo "Testing TopFlight display environment..."
echo "DISPLAY: $DISPLAY"
echo "PROJECT_ROOT: $PROJECT_ROOT"

if xdpyinfo >/dev/null 2>&1; then
    echo "✅ Display :99 is accessible"
    xdpyinfo | grep "dimensions"
else
    echo "❌ Display :99 is not accessible"
    exit 1
fi

if systemctl is-active --quiet xvfb-main; then
    echo "✅ Xvfb service is running"
else
    echo "❌ Xvfb service is not running"
    exit 1
fi

echo "✅ TopFlight display environment is ready!"
EOF

chmod +x "$TEST_SCRIPT"
chown topflight:topflight "$TEST_SCRIPT" 2>/dev/null || true

log "Xvfb setup complete!"
echo ""
echo "✅ TopFlight Xvfb Setup Summary:"
echo "  🖥️  Main Display: :99"
echo "  👤 User: topflight"
echo "  📁 Project Root: $PROJECT_ROOT"
echo "  🔧 Service: xvfb-main.service"
echo "  📋 Logs: $LOGS_DIR/xvfb_setup.log"
echo ""
echo "💡 Next steps:"
echo "  1. Test display: $TEST_SCRIPT"
echo "  2. Restart terminal or run: source ~/.bashrc"
echo "  3. Start TopFlight: cd $PROJECT_ROOT && ./pm2-management.sh start"
echo ""
echo "🔧 Useful commands:"
echo "  sudo systemctl status xvfb-main    # Check service status"
echo "  sudo systemctl restart xvfb-main   # Restart service"
echo "  export DISPLAY=:99 && xdpyinfo     # Test display"
