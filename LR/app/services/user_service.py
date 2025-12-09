import asyncio
import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.cache import USER_CACHE_PREFIX, USER_CACHE_TTL, CacheService
from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserResponse, UserUpdate
from models import User


class UserService:
    """Сервисный слой для работы с пользователями"""

    def __init__(self, user_repository: UserRepository, cache_service: CacheService):
        """
        Инициализация сервиса

        Args:
            user_repository: Репозиторий для работы с пользователями
            cache_service: Сервис для работы с кэшем
        """
        self.user_repository = user_repository
        self.cache_service = cache_service

    async def get_by_id(self, session: AsyncSession, user_id: str) -> Optional[User]:
        """
        Получить пользователя по ID с кэшированием

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)

        Returns:
            User или None, если пользователь не найден
        """
        # Сначала получаем из БД (кэш используется только для оптимизации, не для замены БД)
        user = await self.user_repository.get_by_id(session, user_id)

        # Сохраняем в кэш (с обработкой ошибок и таймаутом)
        if user:
            cache_key = f"{USER_CACHE_PREFIX}{user_id}"
            try:
                user_response = UserResponse.model_validate(user)
                # Используем asyncio.wait_for для таймаута
                await asyncio.wait_for(
                    self.cache_service.set_model(
                        cache_key, user_response, USER_CACHE_TTL
                    ),
                    timeout=0.5,  # Таймаут 500мс для записи в кэш
                )
            except (
                asyncio.TimeoutError,
                ValueError,
                TypeError,
                AttributeError,
                ConnectionError,
            ):
                # Если ошибка при сохранении в кэш, игнорируем и продолжаем
                pass

        return user

    async def get_by_filter(
        self, session: AsyncSession, count: int, page: int, **kwargs
    ) -> list[User]:
        """
        Получить список пользователей с фильтрацией и пагинацией

        Args:
            session: Асинхронная сессия SQLAlchemy
            count: Количество записей на странице
            page: Номер страницы (начиная с 1)
            **kwargs: Параметры фильтрации (username, email, description и т.д.)

        Returns:
            Список пользователей
        """
        return await self.user_repository.get_by_filter(session, count, page, **kwargs)

    async def create(self, session: AsyncSession, user_data: UserCreate) -> User:
        """
        Создать нового пользователя

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_data: Данные для создания пользователя

        Returns:
            Созданный пользователь

        Raises:
            ValueError: Если пользователь с таким username или email уже существует
        """
        # Здесь можно добавить бизнес-логику, например, проверку на существование пользователя
        # На текущий момент просто делегируем репозиторию
        return await self.user_repository.create(session, user_data)

    async def update(
        self, session: AsyncSession, user_id: str, user_data: UserUpdate
    ) -> User:
        """
        Обновить пользователя (удаляем из кэша при обновлении)

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
            user_data: Данные для обновления пользователя

        Returns:
            Обновленный пользователь

        Raises:
            ValueError: Если пользователь не найден
        """
        # Обновляем пользователя в БД
        updated_user = await self.user_repository.update(session, user_id, user_data)
        if updated_user is None:
            raise ValueError(f"User with id {user_id} not found")

        # Удаляем из кэша при обновлении (с обработкой ошибок)
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        try:
            import asyncio

            await asyncio.wait_for(self.cache_service.delete(cache_key), timeout=0.5)
        except (
            asyncio.TimeoutError,
            ValueError,
            TypeError,
            AttributeError,
            ConnectionError,
        ):
            # Если ошибка при удалении из кэша, игнорируем
            pass

        return updated_user

    async def delete(self, session: AsyncSession, user_id: str) -> None:
        """
        Удалить пользователя (удаляем из кэша)

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
        """
        # Удаляем из БД
        await self.user_repository.delete(session, user_id)

        # Удаляем из кэша (с обработкой ошибок)
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        try:
            import asyncio

            await asyncio.wait_for(self.cache_service.delete(cache_key), timeout=0.5)
        except (
            asyncio.TimeoutError,
            ValueError,
            TypeError,
            AttributeError,
            ConnectionError,
        ):
            # Если ошибка при удалении из кэша, игнорируем
            pass
