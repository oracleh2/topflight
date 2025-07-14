import asyncio
from sqlalchemy import select, update
from app.database import async_session_maker
from app.models import User, UserBalance, BalanceTransaction
from decimal import Decimal


async def add_balance_to_user():
    """Добавляет баланс пользователю"""
    async with async_session_maker() as session:
        email = "oracleh2@gmail.com"
        amount = Decimal("10000.00")

        print(f"Добавление баланса пользователю: {email}")

        # Находим пользователя
        result = await session.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()

        if not user:
            print(f"❌ Пользователь с email {email} не найден!")
            return

        # Обновляем баланс в таблице users
        user.balance = amount

        # Обновляем баланс в таблице user_balance
        balance_result = await session.execute(
            select(UserBalance).where(UserBalance.user_id == user.id)
        )
        user_balance = balance_result.scalar_one_or_none()

        if user_balance:
            user_balance.current_balance = amount
            user_balance.last_topup_amount = amount
            user_balance.last_topup_date = user.updated_at

        # Создаем транзакцию пополнения
        transaction = BalanceTransaction(
            user_id=user.id,
            amount=amount,
            type="topup",
            description="Начальный баланс для администратора"
        )

        session.add(transaction)
        await session.commit()

        print(f"✅ Баланс добавлен успешно!")
        print(f"Новый баланс: {amount} руб.")

        print(f"\n🎉 Пользователь готов к работе!")
        print(f"Email: {email}")
        print(f"Password: 12312344")
        print(f"API Key: {user.api_key}")
        print(f"Баланс: {amount} руб.")


if __name__ == "__main__":
    asyncio.run(add_balance_to_user())