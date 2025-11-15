import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path

# Добавляем путь к корневой папке проекта для импорта моделей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Base

# Тестовая база данных
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"


@pytest.fixture(scope="session")
def engine():
    """Создает engine для тестовой БД"""
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="session")
async def tables(engine):
    """Создает и удаляет таблицы для тестов"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def session(engine, tables):
    """Создает сессию для тестов"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Очищаем данные перед каждым тестом
        from sqlalchemy import text
        await session.execute(text("DELETE FROM order_items"))
        await session.execute(text("DELETE FROM orders"))
        await session.execute(text("DELETE FROM addresses"))
        await session.execute(text("DELETE FROM products"))
        await session.execute(text("DELETE FROM users"))
        await session.commit()
        
        yield session
        
        # Очищаем данные после каждого теста
        try:
            await session.execute(text("DELETE FROM order_items"))
            await session.execute(text("DELETE FROM orders"))
            await session.execute(text("DELETE FROM addresses"))
            await session.execute(text("DELETE FROM products"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception:
            await session.rollback()


@pytest.fixture
def user_repository(session):
    """Фикстура для UserRepository"""
    from app.repositories.user_repository import UserRepository
    return UserRepository()


@pytest.fixture
def product_repository(session):
    """Фикстура для ProductRepository"""
    from app.repositories.product_repository import ProductRepository
    return ProductRepository()


@pytest.fixture
def order_repository(session):
    """Фикстура для OrderRepository"""
    from app.repositories.order_repository import OrderRepository
    return OrderRepository()


@pytest.fixture
def client():
    """Фикстура для тестового клиента"""
    from litestar.testing import TestClient
    from app.main import app
    return TestClient(app=app)

