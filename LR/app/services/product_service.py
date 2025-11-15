from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import sys
from pathlib import Path

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Product
from app.repositories.product_repository import ProductRepository
from app.schemas.product import ProductCreate, ProductUpdate


class ProductService:
    """Сервисный слой для работы с продуктами"""

    def __init__(self, product_repository: ProductRepository):
        """
        Инициализация сервиса
        
        Args:
            product_repository: Репозиторий для работы с продуктами
        """
        self.product_repository = product_repository

    async def get_by_id(self, session: AsyncSession, product_id: str) -> Optional[Product]:
        """
        Получить продукт по ID
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
            
        Returns:
            Product или None, если продукт не найден
        """
        return await self.product_repository.get_by_id(session, product_id)

    async def get_all(
        self, 
        session: AsyncSession,
        count: int = 100, 
        page: int = 1
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
        self, 
        session: AsyncSession,
        product_data: ProductCreate
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
        self, 
        session: AsyncSession,
        product_id: str, 
        product_data: ProductUpdate
    ) -> Product:
        """
        Обновить продукт
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
            product_data: Данные для обновления продукта
            
        Returns:
            Обновленный продукт
            
        Raises:
            ValueError: Если продукт не найден
        """
        updated_product = await self.product_repository.update(session, product_id, product_data)
        if updated_product is None:
            raise ValueError(f"Product with id {product_id} not found")
        return updated_product

    async def delete(self, session: AsyncSession, product_id: str) -> None:
        """
        Удалить продукт
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
        """
        await self.product_repository.delete(session, product_id)

