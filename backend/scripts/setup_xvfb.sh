#!/bin/bash
# backend/scripts/setup_xvfb.sh
echo "🚀 Setting up Xvfb for headless browser automation..."

# Функция для проверки установки пакета
check_package() {
    dpkg -l | grep -q "^ii  $1 "
}

# Список необходимых пакетов
REQUIRED_PACKAGES=(
    "xvfb"
    "x11-xserver-utils"
    "xfonts-100dpi"
    "xfonts-75dpi"
    "xfonts-scalable"
    "xfonts-cyrillic"
)

# Проверка каких пакетов не хватает
MISSING_PACKAGES=()
echo "🔍 Checking installed packages..."

for package in "${REQUIRED_PACKAGES[@]}"; do
    if ! check_package "$package"; then
        MISSING_PACKAGES+=("$package")
        echo "❌ Missing: $package"
    else
        echo "✅ Found: $package"
    fi
done

# Установка только недостающих пакетов
if [ ${#MISSING_PACKAGES[@]} -gt 0 ]; then
    echo "📦 Installing missing packages: ${MISSING_PACKAGES[*]}"
    echo "🔄 Updating package list..."
    sudo apt-get update

    echo "📦 Installing packages..."
    sudo apt-get install -y "${MISSING_PACKAGES[@]}"

    if [ $? -eq 0 ]; then
        echo "✅ All packages installed successfully!"
    else
        echo "❌ Failed to install some packages"
        exit 1
    fi
else
    echo "✅ All required packages are already installed!"
fi

# Проверка существования systemd сервиса
if [ ! -f "/etc/systemd/system/xvfb.service" ]; then
    echo "🔧 Creating systemd service..."
    sudo tee /etc/systemd/system/xvfb.service > /dev/null <<EOF
[Unit]
Description=X Virtual Framebuffer
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/bin/Xvfb :99 -screen 0 1920x1080x24 -ac +extension GLX
ExecStop=/bin/kill -TERM \$MAINPID
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
    echo "✅ Systemd service created!"
else
    echo "✅ Systemd service already exists!"
fi

# Запуск и включение сервиса
echo "🔄 Starting Xvfb service..."
sudo systemctl daemon-reload
sudo systemctl enable xvfb

# Проверка статуса сервиса
if sudo systemctl is-active --quiet xvfb; then
    echo "✅ Xvfb service is already running!"
else
    echo "🔄 Starting Xvfb service..."
    sudo systemctl start xvfb
fi

# Проверка статуса
echo "📊 Checking Xvfb status..."
sudo systemctl status xvfb --no-pager

# Установка переменной окружения (только если её нет)
if ! grep -q "export DISPLAY=:99" ~/.bashrc; then
    echo "🌍 Setting up environment variable..."
    echo "export DISPLAY=:99" >> ~/.bashrc
    echo "✅ Environment variable added to ~/.bashrc"
else
    echo "✅ Environment variable already set in ~/.bashrc"
fi

# Проверка работы
echo "🧪 Testing Xvfb..."
export DISPLAY=:99
if command -v xdpyinfo >/dev/null 2>&1; then
    xdpyinfo | head -10
    echo "✅ Xvfb is working correctly!"
else
    echo "⚠️  xdpyinfo not found, but Xvfb should be working"
fi

echo "✅ Xvfb setup complete!"
echo "💡 You can now run: export DISPLAY=:99 && python your_script.py"
echo "💡 Or restart your terminal/IDE to use the new DISPLAY variable"
