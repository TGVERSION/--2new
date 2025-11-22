"""Скрипт для проверки подключения к базе данных"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

async def check_db():
    """Проверка подключения к базе данных"""
    DATABASE_URL = "sqlite+aiosqlite:///./lab2.db"
    engine = create_async_engine(DATABASE_URL, echo=False)
    
    try:
        async with engine.begin() as conn:
            # Проверяем подключение
            result = await conn.execute(text("SELECT 1"))
            print("OK: Подключение к БД успешно")
            
            # Проверяем наличие таблиц
            result = await conn.execute(text(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ))
            tables = [row[0] for row in result.fetchall()]
            print(f"OK: Найдено таблиц: {len(tables)}")
            print(f"  Таблицы: {', '.join(tables)}")
            
            # Проверяем наличие пользователей
            if 'users' in tables:
                result = await conn.execute(text("SELECT COUNT(*) FROM users"))
                count = result.scalar()
                print(f"OK: Пользователей в БД: {count}")
            
    except Exception as e:
        print(f"ERROR: Ошибка: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(check_db())

