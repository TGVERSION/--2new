import pytest
from litestar.testing import create_test_client
from litestar.status_codes import HTTP_200_OK, HTTP_201_CREATED, HTTP_204_NO_CONTENT, HTTP_404_NOT_FOUND
from litestar.di import Provide
from polyfactory.factories.pydantic_factory import ModelFactory
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.user import UserResponse, UserCreate
from app.controllers.user_controller import UserController
from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository
from sqlalchemy.ext.asyncio import AsyncSession


class UserResponseFactory(ModelFactory[UserResponse]):
    """Фабрика для создания тестовых объектов UserResponse"""
    model = UserResponse


@pytest.fixture
def user_service(mock_cache_service):
    """Фикстура для UserService"""
    return UserService(user_repository=UserRepository(), cache_service=mock_cache_service)


@pytest.fixture
def test_client(user_service, session):
    """Фикстура для тестового клиента"""
    async def provide_db_session() -> AsyncSession:
        yield session
    
    async def provide_user_repository() -> UserRepository:
        return UserRepository()
    
    async def provide_user_service() -> UserService:
        return user_service
    
    with create_test_client(
        route_handlers=[UserController],
        dependencies={
            "db_session": Provide(provide_db_session),
            "user_repository": Provide(provide_user_repository),
            "user_service": Provide(provide_user_service),
        }
    ) as client:
        yield client


class TestUserRoutes:
    """Тесты для API endpoints пользователей"""

    @pytest.mark.asyncio
    async def test_get_user_by_id(self, test_client, session, user_service):
        """Тест получения пользователя по ID"""
        # Создаем пользователя
        from app.schemas.user import UserCreate
        user_data = UserCreate(
            username="test_user",
            email="test@example.com",
            description="Test user"
        )
        user = await user_service.create(session, user_data)
        
        # Получаем пользователя через API
        response = test_client.get(f"/users/{user.id}")
        
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["id"] == user.id
        assert data["username"] == "test_user"

    @pytest.mark.asyncio
    async def test_get_all_users(self, test_client, session, user_service):
        """Тест получения списка пользователей"""
        # Создаем несколько пользователей
        from app.schemas.user import UserCreate
        await user_service.create(
            session,
            UserCreate(username="user1", email="user1@example.com")
        )
        await user_service.create(
            session,
            UserCreate(username="user2", email="user2@example.com")
        )
        
        # Получаем список через API
        response = test_client.get("/users")
        
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 2

    def test_create_user(self, test_client):
        """Тест создания пользователя"""
        user_data = {
            "username": "new_user",
            "email": "new@example.com",
            "description": "New user"
        }
        
        response = test_client.post("/users", json=user_data)
        
        assert response.status_code == HTTP_201_CREATED
        data = response.json()
        assert data["username"] == "new_user"
        assert data["email"] == "new@example.com"

    @pytest.mark.asyncio
    async def test_update_user(self, test_client, session, user_service):
        """Тест обновления пользователя"""
        # Создаем пользователя
        from app.schemas.user import UserCreate
        user = await user_service.create(
            session,
            UserCreate(username="update_test", email="update@example.com")
        )
        
        # Обновляем через API
        update_data = {
            "username": "updated_user",
            "email": "updated@example.com",
            "description": "Updated"
        }
        
        response = test_client.put(f"/users/{user.id}", json=update_data)
        
        assert response.status_code == HTTP_200_OK
        data = response.json()
        assert data["username"] == "updated_user"

    @pytest.mark.asyncio
    async def test_delete_user(self, test_client, session, user_service):
        """Тест удаления пользователя"""
        # Создаем пользователя
        from app.schemas.user import UserCreate
        user = await user_service.create(
            session,
            UserCreate(username="delete_test", email="delete@example.com")
        )
        
        # Удаляем через API
        response = test_client.delete(f"/users/{user.id}")
        
        assert response.status_code == HTTP_204_NO_CONTENT
        
        # Проверяем, что пользователь удален
        get_response = test_client.get(f"/users/{user.id}")
        assert get_response.status_code == HTTP_404_NOT_FOUND

