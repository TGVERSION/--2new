import sys
from pathlib import Path
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.repositories.user_repository import UserRepository
from app.schemas.user import UserCreate, UserUpdate
from models import User


class UserService:
    """Сервисный слой для работы с пользователями"""

    def __init__(self, user_repository: UserRepository):
        """
        Инициализация сервиса

        Args:
            user_repository: Репозиторий для работы с пользователями
        """
        self.user_repository = user_repository

    async def get_by_id(self, session: AsyncSession, user_id: str) -> Optional[User]:
        """
        Получить пользователя по ID

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)

        Returns:
            User или None, если пользователь не найден
        """
        return await self.user_repository.get_by_id(session, user_id)

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
        Обновить пользователя

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
            user_data: Данные для обновления пользователя

        Returns:
            Обновленный пользователь

        Raises:
            ValueError: Если пользователь не найден
        """
        # Здесь можно добавить бизнес-логику, например, валидацию данных
        # На текущий момент просто делегируем репозиторию
        updated_user = await self.user_repository.update(session, user_id, user_data)
        if updated_user is None:
            raise ValueError(f"User with id {user_id} not found")
        return updated_user

    async def delete(self, session: AsyncSession, user_id: str) -> None:
        """
        Удалить пользователя

        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
        """
        # Здесь можно добавить бизнес-логику, например, проверку на наличие связанных данных
        # На текущий момент просто делегируем репозиторию
        await self.user_repository.delete(session, user_id)
