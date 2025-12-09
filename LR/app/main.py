import os

from litestar import Litestar
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.cache import CacheService, create_redis_client
from app.controllers.order_controller import OrderController
from app.controllers.product_controller import ProductController
from app.controllers.user_controller import UserController
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.services.order_service import OrderService
from app.services.product_service import ProductService
from app.services.user_service import UserService

# Настройка базы данных
# Используем SQLite с aiosqlite для асинхронной работы
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./lab2.db")

# Создаем асинхронный engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Создаем фабрику сессий
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def provide_db_session() -> AsyncSession:
    """Провайдер сессии базы данных"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Глобальный клиент Redis (singleton pattern)
_redis_client_instance = None  # pylint: disable=global-statement


async def provide_redis_client():
    """Провайдер клиента Redis (singleton)"""
    global _redis_client_instance  # pylint: disable=global-statement
    if _redis_client_instance is None:
        try:
            import asyncio

            _redis_client_instance = await asyncio.wait_for(
                create_redis_client(), timeout=2.0
            )
        except asyncio.TimeoutError:
            print(
                "WARNING: Таймаут при подключении к Redis. Кэширование будет отключено."
            )
            # Создаем фиктивный клиент
            import redis.asyncio as redis_module

            _redis_client_instance = redis_module.Redis(
                host="nonexistent", port=6379, db=0, decode_responses=False
            )
        except (redis_module.RedisError, ConnectionError, OSError) as e:
            print(
                f"WARNING: Ошибка при подключении к Redis: {e}. Кэширование будет отключено."
            )
            # Создаем фиктивный клиент
            import redis.asyncio as redis_module

            _redis_client_instance = redis_module.Redis(
                host="nonexistent", port=6379, db=0, decode_responses=False
            )
    return _redis_client_instance


async def provide_cache_service() -> CacheService:
    """Провайдер сервиса кэша"""
    redis_client = await provide_redis_client()
    return CacheService(redis_client)


async def provide_user_repository(
    db_session: AsyncSession = Provide(provide_db_session),
) -> UserRepository:
    """Провайдер репозитория пользователей"""
    # Note: UserRepository doesn't store session in constructor,
    # but we provide it here for dependency injection chain
    # Session will be passed to methods when called
    return UserRepository()


async def provide_user_service(
    user_repository: UserRepository = Provide(provide_user_repository),
    cache_service: CacheService = Provide(provide_cache_service),
) -> UserService:
    """Провайдер сервиса пользователей"""
    return UserService(user_repository, cache_service)


async def provide_order_repository(
    db_session: AsyncSession = Provide(provide_db_session),
) -> OrderRepository:
    """Провайдер репозитория заказов"""
    return OrderRepository()


async def provide_product_repository(
    db_session: AsyncSession = Provide(provide_db_session),
) -> ProductRepository:
    """Провайдер репозитория продукции"""
    return ProductRepository()


async def provide_order_service(
    order_repository: OrderRepository = Provide(provide_order_repository),
    product_repository: ProductRepository = Provide(provide_product_repository),
    user_repository: UserRepository = Provide(provide_user_repository),
) -> OrderService:
    """Провайдер сервиса заказов"""
    return OrderService(order_repository, product_repository, user_repository)


async def provide_product_service(
    product_repository: ProductRepository = Provide(provide_product_repository),
    cache_service: CacheService = Provide(provide_cache_service),
) -> ProductService:
    """Провайдер сервиса продукции"""
    return ProductService(product_repository, cache_service)


# Конфигурация OpenAPI для генерации схемы API
openapi_config = OpenAPIConfig(
    title="Order and Product Management API",
    version="1.0.0",
    description="API для управления пользователями, заказами и продукцией",
)


app = Litestar(
    route_handlers=[UserController, OrderController, ProductController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository),
        "user_service": Provide(provide_user_service),
        "order_repository": Provide(provide_order_repository),
        "product_repository": Provide(provide_product_repository),
        "order_service": Provide(provide_order_service),
        "product_service": Provide(provide_product_service),
        "redis_client": Provide(provide_redis_client),
        "cache_service": Provide(provide_cache_service),
    },
    openapi_config=openapi_config,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
