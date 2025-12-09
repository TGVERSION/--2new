import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import sys
from pathlib import Path
import os

# Добавляем путь к корневой папке проекта для импорта моделей
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from models import Base

# Тестовая база данных - используем in-memory для параллельных тестов
# или уникальный файл для каждого worker процесса
worker_id = os.environ.get("PYTEST_XDIST_WORKER", "main")
if worker_id == "main":
    TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
else:
    # Для параллельных тестов используем in-memory БД или уникальные файлы
    TEST_DATABASE_URL = f"sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def engine():
    """Создает engine для тестовой БД"""
    return create_async_engine(TEST_DATABASE_URL, echo=True)


@pytest.fixture(scope="session")
async def tables(engine):
    """Создает и удаляет таблицы для тестов"""
    async with engine.begin() as conn:
        # Игнорируем ошибки при удалении (таблицы могут не существовать)
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        # Игнорируем ошибки при удалении
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass


@pytest.fixture
async def session(engine, tables):
    """Создает сессию для тестов"""
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with async_session() as session:
        # Очищаем данные перед каждым тестом
        from sqlalchemy import text
        try:
            await session.execute(text("DELETE FROM order_items"))
            await session.execute(text("DELETE FROM orders"))
            await session.execute(text("DELETE FROM addresses"))
            await session.execute(text("DELETE FROM products"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception:
            await session.rollback()
        
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


@pytest.fixture
def mock_cache_service():
    """Фикстура для мока CacheService"""
    from unittest.mock import AsyncMock, MagicMock
    from app.cache import CacheService
    
    mock_redis = AsyncMock()
    cache_service = CacheService(mock_redis)
    
    # Мокаем методы кэша для проверки вызовов
    cache_service.set_model = AsyncMock(return_value=True)
    cache_service.delete = AsyncMock(return_value=True)
    cache_service.get_model = AsyncMock(return_value=None)
    
    return cache_service


@pytest.fixture
async def redis_client():
    """Фикстура для реального Redis клиента (опционально)"""
    try:
        import redis.asyncio as redis_module
        client = redis_module.Redis(
            host="localhost",
            port=6379,
            db=15,  # Используем отдельную БД для тестов
            decode_responses=False,
            socket_connect_timeout=1,
            socket_timeout=1
        )
        await client.ping()
        yield client
        # Очищаем тестовую БД после тестов
        await client.flushdb()
        await client.aclose()
    except Exception:
        # Если Redis недоступен, возвращаем None
        yield None


@pytest.fixture
async def real_cache_service(redis_client):
    """Фикстура для реального CacheService (если Redis доступен)"""
    if redis_client is None:
        pytest.skip("Redis недоступен, пропускаем тесты с реальным кэшем")
    
    from app.cache import CacheService
    return CacheService(redis_client)

