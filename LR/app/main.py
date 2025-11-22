import os

from litestar import Litestar
from litestar.di import Provide
from litestar.openapi import OpenAPIConfig
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.controllers.user_controller import UserController
from app.repositories.user_repository import UserRepository
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
) -> UserService:
    """Провайдер сервиса пользователей"""
    return UserService(user_repository)


# Конфигурация OpenAPI для генерации схемы API
openapi_config = OpenAPIConfig(
    title="User Management API",
    version="1.0.0",
    description="API для управления пользователями",
)


app = Litestar(
    route_handlers=[UserController],
    dependencies={
        "db_session": Provide(provide_db_session),
        "user_repository": Provide(provide_user_repository),
        "user_service": Provide(provide_user_service),
    },
    openapi_config=openapi_config,
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
