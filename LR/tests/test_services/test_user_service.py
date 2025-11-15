import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository


class TestUserService:
    """Тесты для UserService"""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        """Тест успешного получения пользователя по ID"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.get_by_id.return_value = Mock(
            id="1", username="test", email="test@example.com"
        )
        
        user_service = UserService(user_repository=mock_user_repo)
        
        result = await user_service.get_by_id(None, "1")
        
        assert result is not None
        assert result.id == "1"
        mock_user_repo.get_by_id.assert_called_once_with(None, "1")

    @pytest.mark.asyncio
    async def test_create_user_success(self):
        """Тест успешного создания пользователя"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.create.return_value = Mock(
            id="1", username="test", email="test@example.com"
        )
        
        user_service = UserService(user_repository=mock_user_repo)
        
        from app.schemas.user import UserCreate
        user_data = UserCreate(
            username="test",
            email="test@example.com",
            description="Test user"
        )
        
        result = await user_service.create(None, user_data)
        
        assert result is not None
        assert result.username == "test"
        mock_user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_not_found(self):
        """Тест обновления несуществующего пользователя"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.update.return_value = None
        
        user_service = UserService(user_repository=mock_user_repo)
        
        from app.schemas.user import UserUpdate
        user_data = UserUpdate(username="updated")
        
        with pytest.raises(ValueError, match="not found"):
            await user_service.update(None, "999", user_data)

