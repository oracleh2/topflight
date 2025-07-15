#!/bin/bash

# Создание токена администратора для VNC управления
# scripts/create_admin_token.sh

set -euo pipefail

PROJECT_ROOT="/var/www/topflight"
BACKEND_DIR="$PROJECT_ROOT/backend"

echo "🔐 Creating TopFlight Admin Token..."

# Проверяем окружение
if [ ! -d "$BACKEND_DIR" ]; then
    echo "❌ Backend directory not found: $BACKEND_DIR"
    exit 1
fi

if [ ! -f "$BACKEND_DIR/venv/bin/python" ]; then
    echo "❌ Python virtual environment not found"
    exit 1
fi

cd "$BACKEND_DIR"
source venv/bin/activate

# Создаем временный скрипт для получения токена
cat > /tmp/get_admin_token.py << 'EOF'
import asyncio
import sys
import os
sys.path.insert(0, '/var/www/topflight/backend')

from app.database import async_session_maker
from app.models import User
from app.core.auth import create_access_token
from sqlalchemy import select

async def get_admin_token():
    async with async_session_maker() as session:
        # Находим первого администратора
        result = await session.execute(
            select(User).where(User.is_admin == True).limit(1)
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("❌ No admin user found")
            print("Run: python create_admin_user.py")
            return None

        # Создаем токен
        token = create_access_token(data={"sub": admin.email})

        print("✅ Admin token created successfully!")
        print(f"👤 Admin: {admin.email}")
        print(f"🔑 Token: {token}")
        print("")
        print("💡 Usage:")
        print(f"export ADMIN_TOKEN='{token}'")
        print("./pm2-management.sh debug TASK_ID")
        print("")
        print("🌐 API Test:")
        print(f"curl -H 'Authorization: Bearer {token}' http://localhost:8000/admin/debug/sessions")

        return token

if __name__ == "__main__":
    asyncio.run(get_admin_token())
EOF

# Запускаем скрипт
python /tmp/get_admin_token.py

# Удаляем временный файл
rm -f /tmp/get_admin_token.py
