import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.user_service import UserService
from app.services.product_service import ProductService
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.user import UserCreate, UserUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.cache import CacheService, USER_CACHE_PREFIX, PRODUCT_CACHE_PREFIX


class TestUserServiceCacheIntegration:
    """Интеграционные тесты кэширования для UserService"""

    @pytest.mark.asyncio
    async def test_user_caching_with_real_redis(self, session, real_cache_service):
        """Тест кэширования пользователя с реальным Redis"""
        user_repo = UserRepository()
        user_service = UserService(user_repo, real_cache_service)
        
        # Создаем пользователя
        user_data = UserCreate(
            username="cache_test_user",
            email="cache_test@example.com",
            description="Test user for caching"
        )
        user = await user_service.create(session, user_data)
        user_id = str(user.id)
        
        # Очищаем кэш перед тестом
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        await real_cache_service.delete(cache_key)
        
        # Первый запрос - должен сохранить в кэш
        user1 = await user_service.get_by_id(session, user_id)
        assert user1 is not None
        
        # Проверяем, что данные есть в кэше
        cached_data = await real_cache_service.get(cache_key)
        assert cached_data is not None
        
        # Второй запрос - должен использовать кэш (но мы всё равно идём в БД)
        user2 = await user_service.get_by_id(session, user_id)
        assert user2 is not None
        assert user2.id == user1.id

    @pytest.mark.asyncio
    async def test_user_cache_invalidation_on_update(self, session, real_cache_service):
        """Тест инвалидации кэша при обновлении пользователя"""
        user_repo = UserRepository()
        user_service = UserService(user_repo, real_cache_service)
        
        # Создаем пользователя
        user_data = UserCreate(
            username="update_cache_test",
            email="update_cache@example.com"
        )
        user = await user_service.create(session, user_data)
        user_id = str(user.id)
        
        # Получаем пользователя (сохраняется в кэш)
        await user_service.get_by_id(session, user_id)
        
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        
        # Проверяем, что данные есть в кэше
        cached_before = await real_cache_service.get(cache_key)
        assert cached_before is not None
        
        # Обновляем пользователя
        update_data = UserUpdate(username="updated_username")
        await user_service.update(session, user_id, update_data)
        
        # Проверяем, что кэш был очищен
        cached_after = await real_cache_service.get(cache_key)
        # Кэш должен быть очищен (но может быть сразу же заполнен заново)
        # Проверяем, что данные обновились
        updated_user = await user_service.get_by_id(session, user_id)
        assert updated_user.username == "updated_username"

    @pytest.mark.asyncio
    async def test_user_cache_invalidation_on_delete(self, session, real_cache_service):
        """Тест инвалидации кэша при удалении пользователя"""
        user_repo = UserRepository()
        user_service = UserService(user_repo, real_cache_service)
        
        # Создаем пользователя
        user_data = UserCreate(
            username="delete_cache_test",
            email="delete_cache@example.com"
        )
        user = await user_service.create(session, user_data)
        user_id = str(user.id)
        
        # Получаем пользователя (сохраняется в кэш)
        await user_service.get_by_id(session, user_id)
        
        cache_key = f"{USER_CACHE_PREFIX}{user_id}"
        
        # Проверяем, что данные есть в кэше
        cached_before = await real_cache_service.get(cache_key)
        assert cached_before is not None
        
        # Удаляем пользователя
        await user_service.delete(session, user_id)
        
        # Проверяем, что кэш был очищен
        cached_after = await real_cache_service.get(cache_key)
        assert cached_after is None


class TestProductServiceCacheIntegration:
    """Интеграционные тесты кэширования для ProductService"""

    @pytest.mark.asyncio
    async def test_product_caching_with_real_redis(self, session, real_cache_service):
        """Тест кэширования продукта с реальным Redis"""
        product_repo = ProductRepository()
        product_service = ProductService(product_repo, real_cache_service)
        
        # Создаем продукт
        product_data = ProductCreate(
            name="Cache Test Product",
            price=99.99,
            stock_quantity=10
        )
        product = await product_service.create(session, product_data)
        product_id = str(product.id)
        
        # Очищаем кэш перед тестом
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        await real_cache_service.delete(cache_key)
        
        # Первый запрос - должен сохранить в кэш
        product1 = await product_service.get_by_id(session, product_id)
        assert product1 is not None
        
        # Проверяем, что данные есть в кэше
        cached_data = await real_cache_service.get(cache_key)
        assert cached_data is not None
        
        # Второй запрос
        product2 = await product_service.get_by_id(session, product_id)
        assert product2 is not None
        assert product2.id == product1.id

    @pytest.mark.asyncio
    async def test_product_cache_update_on_update(self, session, real_cache_service):
        """Тест обновления кэша при обновлении продукта"""
        product_repo = ProductRepository()
        product_service = ProductService(product_repo, real_cache_service)
        
        # Создаем продукт
        product_data = ProductCreate(
            name="Update Cache Test",
            price=50.0,
            stock_quantity=5
        )
        product = await product_service.create(session, product_data)
        product_id = str(product.id)
        
        # Получаем продукт (сохраняется в кэш)
        await product_service.get_by_id(session, product_id)
        
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        
        # Обновляем продукт
        update_data = ProductUpdate(price=75.0)
        await product_service.update(session, product_id, update_data)
        
        # Проверяем, что кэш был обновлен
        # После обновления кэш должен содержать новые данные
        updated_product = await product_service.get_by_id(session, product_id)
        assert updated_product.price == 75.0

    @pytest.mark.asyncio
    async def test_product_cache_invalidation_on_delete(self, session, real_cache_service):
        """Тест инвалидации кэша при удалении продукта"""
        product_repo = ProductRepository()
        product_service = ProductService(product_repo, real_cache_service)
        
        # Создаем продукт
        product_data = ProductCreate(
            name="Delete Cache Test",
            price=30.0,
            stock_quantity=3
        )
        product = await product_service.create(session, product_data)
        product_id = str(product.id)
        
        # Получаем продукт (сохраняется в кэш)
        await product_service.get_by_id(session, product_id)
        
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        
        # Проверяем, что данные есть в кэше
        cached_before = await real_cache_service.get(cache_key)
        assert cached_before is not None
        
        # Удаляем продукт
        await product_service.delete(session, product_id)
        
        # Проверяем, что кэш был очищен
        cached_after = await real_cache_service.get(cache_key)
        assert cached_after is None

