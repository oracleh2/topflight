import asyncio
from app.database import async_session_maker
from app.core.user_service import UserService
from app.models import User


async def create_admin_user():
    """Создает пользователя-администратора"""
    async with async_session_maker() as session:
        user_service = UserService(session)

        email = "oracleh2@gmail.com"
        password = "12312344"

        print(f"Создание пользователя-администратора: {email}")

        # Создаем пользователя
        result = await user_service.create_user(
            email=email,
            password=password,
            subscription_plan="premium"  # Сразу премиум план
        )

        if result["success"]:
            print(f"✅ Пользователь создан успешно!")
            print(f"User ID: {result['user_id']}")
            print(f"API Key: {result['api_key']}")

            # Добавим пользователю баланс
            user_id = result['user_id']
            balance_result = await user_service.add_balance(
                user_id=user_id,
                amount=10000.00,  # 10000 рублей
                description="Начальный баланс для администратора"
            )

            if balance_result["success"]:
                print(f"✅ Добавлен баланс: 10000.00 руб.")

            print(f"\n🔑 Данные для входа:")
            print(f"Email: {email}")
            print(f"Password: {password}")
            print(f"API Key: {result['api_key']}")

        else:
            print(f"❌ Ошибка создания пользователя:")
            for error in result["errors"]:
                print(f"  - {error}")


if __name__ == "__main__":
    asyncio.run(create_admin_user())