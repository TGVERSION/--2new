from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete
from typing import Optional
import sys
import os
from pathlib import Path

# Добавляем путь к корневой папке проекта для импорта моделей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import User
from app.schemas.user import UserCreate, UserUpdate


class UserRepository:
    """Репозиторий для работы с пользователями"""

    async def get_by_id(self, session: AsyncSession, user_id: str) -> Optional[User]:
        """
        Получить пользователя по ID
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
            
        Returns:
            User или None, если пользователь не найден
        """
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, session: AsyncSession, email: str) -> Optional[User]:
        """
        Получить пользователя по email
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            email: Email пользователя
            
        Returns:
            User или None, если пользователь не найден
        """
        result = await session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_filter(
        self, 
        session: AsyncSession, 
        count: int, 
        page: int, 
        **kwargs
    ) -> list[User]:
        """
        Получить список пользователей с фильтрацией и пагинацией
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            count: Количество записей на странице
            page: Номер страницы (начиная с 1)
            **kwargs: Параметры фильтрации (username, email, description и т.д.)
                     Поддерживаются точное совпадение и частичный поиск для строковых полей
            
        Returns:
            Список пользователей
        """
        query = select(User)
        
        # Применяем фильтры из kwargs
        if kwargs:
            filters = []
            for key, value in kwargs.items():
                if value is not None and hasattr(User, key):
                    attr = getattr(User, key)
                    # Для строковых полей используем частичный поиск (ilike)
                    # Для других полей - точное совпадение
                    if key in ('username', 'email', 'description'):
                        filters.append(attr.ilike(f"%{value}%"))
                    else:
                        filters.append(attr == value)
            
            if filters:
                query = query.where(*filters)
        
        # Применяем пагинацию
        offset = (page - 1) * count if page > 0 else 0
        query = query.offset(offset).limit(count)
        
        # Выполняем запрос
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(self, session: AsyncSession, user_data: UserCreate = None, **kwargs) -> User:
        """
        Создать нового пользователя
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            user_data: Данные для создания пользователя (опционально)
            **kwargs: Данные для создания пользователя (если user_data не передан)
            
        Returns:
            Созданный пользователь
        """
        if user_data is None:
            # Если передан kwargs, создаем UserCreate из kwargs
            user_data = UserCreate(**kwargs)
        
        user = User(
            username=user_data.username,
            email=user_data.email,
            description=user_data.description
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

    async def update(
        self, 
        session: AsyncSession, 
        user_id: str, 
        user_data: UserUpdate = None,
        **kwargs
    ) -> Optional[User]:
        """
        Обновить пользователя
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
            user_data: Данные для обновления пользователя (опционально)
            **kwargs: Данные для обновления пользователя (если user_data не передан)
            
        Returns:
            Обновленный пользователь или None, если пользователь не найден
        """
        # Получаем пользователя
        user = await self.get_by_id(session, user_id)
        if not user:
            return None
        
        # Если передан kwargs, создаем UserUpdate из kwargs
        if user_data is None:
            user_data = UserUpdate(**kwargs)
        
        # Обновляем только переданные поля
        update_data = user_data.model_dump(exclude_unset=True)
        if not update_data:
            return user
        
        # Обновляем поля
        for field, value in update_data.items():
            setattr(user, field, value)
        
        await session.commit()
        await session.refresh(user)
        return user

    async def delete(self, session: AsyncSession, user_id: str) -> None:
        """
        Удалить пользователя
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            user_id: ID пользователя (UUID в виде строки)
        """
        await session.execute(
            delete(User).where(User.id == user_id)
        )
        await session.commit()

