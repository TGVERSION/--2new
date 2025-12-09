import pytest
from unittest.mock import Mock, AsyncMock, patch
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.user_service import UserService
from app.repositories.user_repository import UserRepository


class TestUserService:
    """Тесты для UserService"""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self, mock_cache_service):
        """Тест успешного получения пользователя по ID"""
        from datetime import datetime
        from models import User
        
        mock_user_repo = AsyncMock(spec=UserRepository)
        # Создаем реальный объект User для теста
        user = User(
            id="1",
            username="test",
            email="test@example.com",
            description=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_user_repo.get_by_id.return_value = user
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
        result = await user_service.get_by_id(None, "1")
        
        assert result is not None
        assert result.id == "1"
        mock_user_repo.get_by_id.assert_called_once_with(None, "1")

    @pytest.mark.asyncio
    async def test_create_user_success(self, mock_cache_service):
        """Тест успешного создания пользователя"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.create.return_value = Mock(
            id="1", username="test", email="test@example.com"
        )
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
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
    async def test_update_user_not_found(self, mock_cache_service):
        """Тест обновления несуществующего пользователя"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.update.return_value = None
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
        from app.schemas.user import UserUpdate
        user_data = UserUpdate(username="updated")
        
        with pytest.raises(ValueError, match="not found"):
            await user_service.update(None, "999", user_data)

    @pytest.mark.asyncio
    async def test_get_by_id_caches_result(self, mock_cache_service):
        """Тест кэширования результата get_by_id"""
        from datetime import datetime
        from models import User
        
        mock_user_repo = AsyncMock(spec=UserRepository)
        user = User(
            id="1",
            username="test",
            email="test@example.com",
            description=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_user_repo.get_by_id.return_value = user
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
        # Первый вызов - должен сохранить в кэш
        result1 = await user_service.get_by_id(None, "1")
        assert result1 is not None
        
        # Проверяем, что set_model был вызван для сохранения в кэш
        assert mock_cache_service.set_model.called

    @pytest.mark.asyncio
    async def test_update_invalidates_cache(self, mock_cache_service):
        """Тест инвалидации кэша при обновлении пользователя"""
        from datetime import datetime
        from models import User
        
        mock_user_repo = AsyncMock(spec=UserRepository)
        user = User(
            id="1",
            username="updated",
            email="test@example.com",
            description=None,
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_user_repo.update.return_value = user
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
        from app.schemas.user import UserUpdate
        user_data = UserUpdate(username="updated")
        
        result = await user_service.update(None, "1", user_data)
        
        assert result is not None
        # Проверяем, что delete был вызван для инвалидации кэша
        assert mock_cache_service.delete.called

    @pytest.mark.asyncio
    async def test_delete_invalidates_cache(self, mock_cache_service):
        """Тест инвалидации кэша при удалении пользователя"""
        mock_user_repo = AsyncMock(spec=UserRepository)
        mock_user_repo.delete.return_value = None
        
        user_service = UserService(user_repository=mock_user_repo, cache_service=mock_cache_service)
        
        await user_service.delete(None, "1")
        
        # Проверяем, что delete был вызван для инвалидации кэша
        assert mock_cache_service.delete.called

