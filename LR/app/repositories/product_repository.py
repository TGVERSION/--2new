import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта моделей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.product import ProductCreate, ProductUpdate
from models import Product


class ProductRepository:
    """Репозиторий для работы с продуктами"""

    async def get_by_id(
        self, session: AsyncSession, product_id: str
    ) -> Optional[Product]:
        """
        Получить продукт по ID

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)

        Returns:
            Product или None, если продукт не найден
        """
        result = await session.execute(select(Product).where(Product.id == product_id))
        return result.scalar_one_or_none()

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
        offset = (page - 1) * count if page > 0 else 0
        query = select(Product).offset(offset).limit(count)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(
        self, session: AsyncSession, product_data: ProductCreate = None, **kwargs
    ) -> Product:
        """
        Создать новый продукт

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_data: Данные для создания продукта (опционально)
            **kwargs: Данные для создания продукта (если product_data не передан)

        Returns:
            Созданный продукт
        """
        if product_data is None:
            product_data = ProductCreate(**kwargs)

        product = Product(
            name=product_data.name,
            description=product_data.description,
            price=product_data.price,
            stock_quantity=product_data.stock_quantity,
        )
        session.add(product)
        await session.commit()
        await session.refresh(product)
        return product

    async def update(
        self,
        session: AsyncSession,
        product_id: str,
        product_data: ProductUpdate = None,
        **kwargs,
    ) -> Optional[Product]:
        """
        Обновить продукт

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
            product_data: Данные для обновления продукта (опционально)
            **kwargs: Данные для обновления продукта (если product_data не передан)

        Returns:
            Обновленный продукт или None, если продукт не найден
        """
        # Получаем продукт
        product = await self.get_by_id(session, product_id)
        if not product:
            return None

        # Если передан kwargs, создаем ProductUpdate из kwargs
        if product_data is None:
            product_data = ProductUpdate(**kwargs)

        # Обновляем только переданные поля
        update_data = product_data.model_dump(exclude_unset=True)
        if not update_data:
            return product

        # Обновляем поля
        for field, value in update_data.items():
            setattr(product, field, value)

        await session.commit()
        await session.refresh(product)
        return product

    async def delete(self, session: AsyncSession, product_id: str) -> None:
        """
        Удалить продукт

        Args:
            session: Асинхронная сессия SQLAlchemy
            product_id: ID продукта (UUID в виде строки)
        """
        await session.execute(delete(Product).where(Product.id == product_id))
        await session.commit()
