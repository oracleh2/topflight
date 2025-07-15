import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def test_and_create():
    engine = create_async_engine("postgresql+asyncpg://parser_user:parser_password@topflight_postgres:5432/yandex_parser")
    try:
        async with engine.connect() as conn:
            # Тест подключения
            result = await conn.execute(text("SELECT 1"))
            print("✅ Подключение из Docker сети успешно!")
            
            # Создаем простую тестовую таблицу
            await conn.execute(text("""
                CREATE TABLE IF NOT EXISTS test_table (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255)
                )
            """))
            await conn.commit()
            print("✅ Тестовая таблица создана!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        await engine.dispose()

asyncio.run(test_and_create())
