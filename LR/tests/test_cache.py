import pytest
import json
from unittest.mock import AsyncMock, Mock, patch
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.cache import CacheService, USER_CACHE_TTL, PRODUCT_CACHE_TTL
from app.schemas.user import UserResponse
from app.schemas.product import ProductResponse
from datetime import datetime


class TestCacheService:
    """Тесты для CacheService"""

    @pytest.fixture
    def mock_redis_client(self):
        """Фикстура для мока Redis клиента"""
        mock_client = AsyncMock()
        return mock_client

    @pytest.fixture
    def cache_service(self, mock_redis_client):
        """Фикстура для CacheService"""
        return CacheService(mock_redis_client)

    @pytest.mark.asyncio
    async def test_get_success(self, cache_service, mock_redis_client):
        """Тест успешного получения значения из кэша"""
        mock_redis_client.get.return_value = b"test_value"
        
        result = await cache_service.get("test_key")
        
        assert result == "test_value"
        mock_redis_client.get.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_get_not_found(self, cache_service, mock_redis_client):
        """Тест получения несуществующего ключа"""
        mock_redis_client.get.return_value = None
        
        result = await cache_service.get("nonexistent_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_get_timeout(self, cache_service, mock_redis_client):
        """Тест обработки таймаута при получении"""
        import asyncio
        mock_redis_client.get.side_effect = asyncio.TimeoutError()
        
        result = await cache_service.get("test_key")
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_success(self, cache_service, mock_redis_client):
        """Тест успешной установки значения в кэш"""
        mock_redis_client.setex.return_value = True
        
        result = await cache_service.set("test_key", "test_value", 3600)
        
        assert result is True
        mock_redis_client.setex.assert_called_once_with("test_key", 3600, "test_value")

    @pytest.mark.asyncio
    async def test_set_timeout(self, cache_service, mock_redis_client):
        """Тест обработки таймаута при установке"""
        import asyncio
        mock_redis_client.setex.side_effect = asyncio.TimeoutError()
        
        result = await cache_service.set("test_key", "test_value", 3600)
        
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_success(self, cache_service, mock_redis_client):
        """Тест успешного удаления ключа из кэша"""
        mock_redis_client.delete.return_value = 1
        
        result = await cache_service.delete("test_key")
        
        assert result is True
        mock_redis_client.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_not_found(self, cache_service, mock_redis_client):
        """Тест удаления несуществующего ключа"""
        mock_redis_client.delete.return_value = 0
        
        result = await cache_service.delete("nonexistent_key")
        
        assert result is True  # delete возвращает True даже если ключа нет

    @pytest.mark.asyncio
    async def test_get_model_success(self, cache_service, mock_redis_client):
        """Тест успешного получения модели из кэша"""
        user_data = {
            "id": "123",
            "username": "test_user",
            "email": "test@example.com",
            "description": "Test",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
        mock_redis_client.get.return_value = json.dumps(user_data).encode("utf-8")
        
        result = await cache_service.get_model("user:123", UserResponse)
        
        assert result is not None
        assert isinstance(result, UserResponse)
        assert result.id == "123"
        assert result.username == "test_user"

    @pytest.mark.asyncio
    async def test_get_model_invalid_json(self, cache_service, mock_redis_client):
        """Тест получения модели с невалидным JSON"""
        mock_redis_client.get.return_value = b"invalid json"
        
        result = await cache_service.get_model("user:123", UserResponse)
        
        assert result is None

    @pytest.mark.asyncio
    async def test_set_model_success(self, cache_service, mock_redis_client):
        """Тест успешного сохранения модели в кэш"""
        user = UserResponse(
            id="123",
            username="test_user",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        mock_redis_client.setex.return_value = True
        
        result = await cache_service.set_model("user:123", user, USER_CACHE_TTL)
        
        assert result is True
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args
        assert call_args[0][0] == "user:123"
        assert call_args[0][1] == USER_CACHE_TTL
        # Проверяем, что значение - это JSON
        stored_value = call_args[0][2]
        assert isinstance(stored_value, str)
        parsed = json.loads(stored_value)
        assert parsed["id"] == "123"

    @pytest.mark.asyncio
    async def test_ping_success(self, cache_service, mock_redis_client):
        """Тест успешной проверки подключения"""
        mock_redis_client.ping.return_value = True
        
        result = await cache_service.ping()
        
        assert result is True
        mock_redis_client.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_ping_failure(self, cache_service, mock_redis_client):
        """Тест проверки подключения при ошибке"""
        import redis.asyncio as redis_module
        mock_redis_client.ping.side_effect = redis_module.RedisError("Connection failed")
        
        result = await cache_service.ping()
        
        assert result is False


class TestCacheServiceIntegration:
    """Интеграционные тесты для CacheService с реальным Redis"""

    @pytest.fixture
    async def redis_client(self):
        """Фикстура для реального Redis клиента"""
        import redis.asyncio as redis_module
        client = redis_module.Redis(
            host="localhost",
            port=6379,
            db=15,  # Используем отдельную БД для тестов
            decode_responses=False
        )
        try:
            await client.ping()
            yield client
        except Exception:
            pytest.skip("Redis недоступен, пропускаем интеграционные тесты")
        finally:
            # Очищаем тестовую БД
            try:
                await client.flushdb()
                await client.aclose()
            except Exception:
                pass

    @pytest.fixture
    def cache_service(self, redis_client):
        """Фикстура для CacheService с реальным Redis"""
        return CacheService(redis_client)

    @pytest.mark.asyncio
    async def test_integration_set_and_get(self, cache_service):
        """Интеграционный тест установки и получения значения"""
        # Устанавливаем значение
        result = await cache_service.set("test_key", "test_value", 60)
        assert result is True
        
        # Получаем значение
        value = await cache_service.get("test_key")
        assert value == "test_value"

    @pytest.mark.asyncio
    async def test_integration_ttl(self, cache_service):
        """Интеграционный тест TTL"""
        # Устанавливаем значение с коротким TTL
        await cache_service.set("ttl_key", "ttl_value", 2)
        
        # Проверяем, что значение есть
        value = await cache_service.get("ttl_key")
        assert value == "ttl_value"
        
        # Ждем истечения TTL
        import asyncio
        await asyncio.sleep(3)
        
        # Проверяем, что значение исчезло
        value = await cache_service.get("ttl_key")
        assert value is None

    @pytest.mark.asyncio
    async def test_integration_model_caching(self, cache_service):
        """Интеграционный тест кэширования модели"""
        user = UserResponse(
            id="test_123",
            username="test_user",
            email="test@example.com",
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Сохраняем модель
        result = await cache_service.set_model("user:test_123", user, 60)
        assert result is True
        
        # Получаем модель
        cached_user = await cache_service.get_model("user:test_123", UserResponse)
        assert cached_user is not None
        assert cached_user.id == "test_123"
        assert cached_user.username == "test_user"
        assert cached_user.email == "test@example.com"

    @pytest.mark.asyncio
    async def test_integration_delete(self, cache_service):
        """Интеграционный тест удаления из кэша"""
        # Устанавливаем значение
        await cache_service.set("delete_key", "delete_value", 60)
        
        # Проверяем, что значение есть
        value = await cache_service.get("delete_key")
        assert value == "delete_value"
        
        # Удаляем значение
        result = await cache_service.delete("delete_key")
        assert result is True
        
        # Проверяем, что значение удалено
        value = await cache_service.get("delete_key")
        assert value is None

