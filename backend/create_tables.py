import asyncio
from app.database import engine
from app.models.base import Base
from app.config import settings


async def create_tables():
    """Создает все таблицы в базе данных"""
    print(f"Подключение к: {settings.effective_database_url}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    print("Таблицы созданы!")


if __name__ == "__main__":
    asyncio.run(create_tables())
