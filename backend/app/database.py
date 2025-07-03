# backend/app/database.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker # type: ignore
from sqlalchemy.orm import DeclarativeBase # type: ignore
from .config import settings

engine = create_async_engine(
    settings.effective_database_url,  # Используем новое свойство
    echo=settings.debug,
    future=True
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()