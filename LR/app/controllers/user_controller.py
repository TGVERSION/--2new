from litestar import Controller, get, post, put, delete
from litestar.params import Parameter
from litestar.exceptions import NotFoundException
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

import sys
from pathlib import Path

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.user_service import UserService
from app.schemas.user import UserCreate, UserUpdate, UserResponse
from models import User


class UserController(Controller):
    """Контроллер для управления пользователями"""
    
    path = "/users"
    tags = ["users"]

    @get("/{user_id:str}")
    async def get_user_by_id(
        self,
        db_session: AsyncSession,
        user_service: UserService,
        user_id: str,
    ) -> UserResponse:
        """
        Получить пользователя по ID
        
        Args:
            user_id: ID пользователя (UUID в формате строки)
            db_session: Сессия базы данных (dependency injection)
            user_service: Сервис для работы с пользователями (dependency injection)
            
        Returns:
            Данные пользователя
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        user = await user_service.get_by_id(db_session, user_id)
        if not user:
            raise NotFoundException(detail=f"User with ID {user_id} not found")
        return UserResponse.model_validate(user)

    @get()
    async def get_all_users(
        self,
        db_session: AsyncSession,
        user_service: UserService,
        page: int = Parameter(default=1, ge=1),
        count: int = Parameter(default=10, ge=1, le=100),
        username: Optional[str] = None,
        email: Optional[str] = None,
        description: Optional[str] = None,
    ) -> List[UserResponse]:
        """
        Получить список всех пользователей
        
        Args:
            db_session: Сессия базы данных (dependency injection)
            user_service: Сервис для работы с пользователями (dependency injection)
            
        Returns:
            Список пользователей
        """
        # Формируем kwargs для фильтрации
        kwargs = {}
        if username is not None:
            kwargs["username"] = username
        if email is not None:
            kwargs["email"] = email
        if description is not None:
            kwargs["description"] = description
        
        users = await user_service.get_by_filter(db_session, count, page, **kwargs)
        return [UserResponse.model_validate(user) for user in users]

    @post()
    async def create_user(
        self,
        data: UserCreate,
        db_session: AsyncSession,
        user_service: UserService,
    ) -> UserResponse:
        """
        Создать нового пользователя
        
        Args:
            data: Данные для создания пользователя
            db_session: Сессия базы данных (dependency injection)
            user_service: Сервис для работы с пользователями (dependency injection)
            
        Returns:
            Созданный пользователь
        """
        user = await user_service.create(db_session, data)
        return UserResponse.model_validate(user)

    @delete("/{user_id:str}")
    async def delete_user(
        self,
        db_session: AsyncSession,
        user_service: UserService,
        user_id: str,
    ) -> None:
        """
        Удалить пользователя
        
        Args:
            user_id: ID пользователя (UUID в формате строки)
            db_session: Сессия базы данных (dependency injection)
            user_service: Сервис для работы с пользователями (dependency injection)
        """
        await user_service.delete(db_session, user_id)

    @put("/{user_id:str}")
    async def update_user(
        self,
        data: UserCreate,  # В требованиях указан UserCreate, но логичнее UserUpdate
        db_session: AsyncSession,
        user_service: UserService,
        user_id: str,
    ) -> UserResponse:
        """
        Обновить пользователя
        
        Args:
            user_id: ID пользователя (UUID в формате строки)
            data: Данные для обновления пользователя
            db_session: Сессия базы данных (dependency injection)
            user_service: Сервис для работы с пользователями (dependency injection)
            
        Returns:
            Обновленный пользователь
            
        Raises:
            NotFoundException: Если пользователь не найден
        """
        # Конвертируем UserCreate в UserUpdate для частичного обновления
        # В требованиях указан UserCreate, но для update логичнее UserUpdate
        user_update = UserUpdate(
            username=data.username,
            email=data.email,
            description=data.description
        )
        
        try:
            user = await user_service.update(db_session, user_id, user_update)
            return UserResponse.model_validate(user)
        except ValueError as e:
            raise NotFoundException(detail=str(e))
