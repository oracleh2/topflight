import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from app.models.base import Base

# Подключаемся как postgres (суперпользователь)
POSTGRES_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/yandex_parser"


async def create_tables():
    """Создает все таблицы в базе данных"""
    print(f"Подключение к: {POSTGRES_URL}")

    engine = create_async_engine(POSTGRES_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    await engine.dispose()
    print("Таблицы созданы!")


if __name__ == "__main__":
    asyncio.run(create_tables())
