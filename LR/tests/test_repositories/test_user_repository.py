import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import User
from app.repositories.user_repository import UserRepository


class TestUserRepository:
    """Тесты для UserRepository"""

    @pytest.mark.asyncio
    async def test_create_user(self, user_repository: UserRepository, session):
        """Тест создания пользователя в репозитории"""
        user_data = {
            "email": "test@example.com",
            "username": "john_doe",
            "description": "Test user"
        }
        
        user = await user_repository.create(session, **user_data)
        
        assert user.id is not None
        assert user.email == "test@example.com"
        assert user.username == "john_doe"
        assert user.description == "Test user"

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repository: UserRepository, session):
        """Тест получения пользователя по email"""
        # Сначала создаем пользователя
        user = await user_repository.create(
            session,
            email="unique@example.com",
            username="user_test",
            description="Test user",
        )
        
        # Затем ищем по email
        found_user = await user_repository.get_by_email(session, "unique@example.com")
        
        assert found_user is not None
        assert found_user.id == user.id
        assert found_user.email == "unique@example.com"

    @pytest.mark.asyncio
    async def test_update_user(self, user_repository: UserRepository, session):
        """Тест обновления пользователя"""
        user = await user_repository.create(
            session,
            email="update@example.com",
            username="test",
            description="Original description",
        )
        
        updated_user = await user_repository.update(session, user.id, description="Updated description")
        
        assert updated_user.username == "test"
        assert updated_user.description == "Updated description"
        assert updated_user.email == "update@example.com"  # не изменилось

    @pytest.mark.asyncio
    async def test_delete_user(self, user_repository: UserRepository, session):
        """Тест удаления пользователя"""
        user = await user_repository.create(
            session,
            email="delete@example.com",
            username="delete_test",
            description="Delete test user",
        )
        user_id = user.id
        
        await user_repository.delete(session, user_id)
        
        deleted_user = await user_repository.get_by_id(session, user_id)
        assert deleted_user is None

    @pytest.mark.asyncio
    async def test_get_all_users(self, user_repository: UserRepository, session):
        """Тест получения списка пользователей"""
        # Создаем несколько пользователей
        await user_repository.create(
            session,
            email="user1@example.com",
            username="user1",
            description="User one",
        )
        await user_repository.create(
            session,
            email="user2@example.com",
            username="user2",
            description="User two",
        )
        
        users = await user_repository.get_by_filter(session, count=10, page=1)
        
        assert len(users) >= 2

