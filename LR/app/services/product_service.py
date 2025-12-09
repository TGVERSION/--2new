import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.cache import PRODUCT_CACHE_PREFIX, PRODUCT_CACHE_TTL, CacheService
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from models import Product


class ProductService:
    """Сервисный слой для работы с продуктами"""

    def __init__(
        self, product_repository: ProductRepository, cache_service: CacheService
    ):
        """
        Инициализация сервиса

        Args:
            product_repository: Репозиторий для работы с продуктами
            cache_service: Сервис для работы с кэшем
        """
        self.product_repository = product_repository
        self.cache_service = cache_service

    async def get_by_id(
        self, session: AsyncSession, product_id: str
    ) -> Optional[Product]:
        """
        Получить продукт по ID с кэшированием

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)

        Returns:
            Product или None, если продукт не найден
        """
        # Проверяем кэш
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        cached_product = await self.cache_service.get_model(cache_key, ProductResponse)

        if cached_product:
            # Если данные есть в кэше, всё равно получаем из БД для валидации
            # и чтобы вернуть объект SQLAlchemy модели
            product = await self.product_repository.get_by_id(session, product_id)
            if product:
                return product

        # Если в кэше нет, получаем из БД
        product = await self.product_repository.get_by_id(session, product_id)

        # Сохраняем в кэш
        if product:
            product_response = ProductResponse.model_validate(product)
            await self.cache_service.set_model(
                cache_key, product_response, PRODUCT_CACHE_TTL
            )

        return product

    async def get_all(
        self, session: AsyncSession, count: int = 100, page: int = 1
    ) -> List[Product]:
        """
        Получить список всех продуктов с пагинацией

        Args:
            session: Асинхронная сессия SQLAlchemy
            count: Количество записей на странице
            page: Номер страницы (начиная с 1)

        Returns:
            Список продуктов
        """
        return await self.product_repository.get_all(session, count, page)

    async def create(
        self, session: AsyncSession, product_data: ProductCreate
    ) -> Product:
        """
        Создать новый продукт

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_data: Данные для создания продукта

        Returns:
            Созданный продукт
        """
        return await self.product_repository.create(session, product_data)

    async def update(
        self, session: AsyncSession, product_id: str, product_data: ProductUpdate
    ) -> Product:
        """
        Обновить продукт (обновляем кэш при обновлении)

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
            product_data: Данные для обновления продукта

        Returns:
            Обновленный продукт

        Raises:
            ValueError: Если продукт не найден
        """
        # Обновляем продукт в БД
        updated_product = await self.product_repository.update(
            session, product_id, product_data
        )
        if updated_product is None:
            raise ValueError(f"Product with id {product_id} not found")

        # Обновляем кэш при обновлении
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        product_response = ProductResponse.model_validate(updated_product)
        await self.cache_service.set_model(
            cache_key, product_response, PRODUCT_CACHE_TTL
        )

        return updated_product

    async def delete(self, session: AsyncSession, product_id: str) -> None:
        """
        Удалить продукт (удаляем из кэша)

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
        """
        # Удаляем из БД
        await self.product_repository.delete(session, product_id)

        # Удаляем из кэша
        cache_key = f"{PRODUCT_CACHE_PREFIX}{product_id}"
        await self.cache_service.delete(cache_key)
