# backend/clean_database.py

import asyncio
import sqlalchemy as sa
from app.database import engine


async def clean_database():
    """Полный сброс схемы public в PostgreSQL"""

    print("🧨 Удаление схемы public и всего содержимого...")

    async with engine.begin() as conn:
        # Отключить все подключения к текущей базе (опционально, если БД используется)
        # await conn.execute(sa.text("SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = current_database() AND pid <> pg_backend_pid()"))

        # Удалить схему со всеми объектами
        await conn.execute(sa.text("DROP SCHEMA public CASCADE"))

        # Воссоздать схему
        await conn.execute(sa.text("CREATE SCHEMA public"))

        # Восстановить разрешения (если нужно)
        await conn.execute(sa.text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(sa.text("GRANT ALL ON SCHEMA public TO public"))

    print("✅ Схема очищена полностью!")


if __name__ == "__main__":
    asyncio.run(clean_database())
