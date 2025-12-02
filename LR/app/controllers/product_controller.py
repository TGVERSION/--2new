"""Контроллер для управления продукцией"""

import sys
from pathlib import Path
from typing import List

from litestar import Controller, get
from litestar.exceptions import NotFoundException
from litestar.params import Parameter
from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.product import ProductResponse
from app.services.product_service import ProductService


class ProductController(Controller):
    """Контроллер для управления продукцией"""

    path = "/products"
    tags = ["products"]

    @get("/{product_id:str}")
    async def get_product_by_id(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        product_id: str,
    ) -> ProductResponse:
        """
        Получить продукцию по ID

        Args:
            product_id: ID продукции (UUID в формате строки)
            db_session: Сессия базы данных (dependency injection)
            product_service: Сервис для работы с продукцией (dependency injection)

        Returns:
            Данные продукции

        Raises:
            NotFoundException: Если продукция не найдена
        """
        product = await product_service.get_by_id(db_session, product_id)
        if not product:
            raise NotFoundException(detail=f"Product with ID {product_id} not found")
        return ProductResponse.model_validate(product)

    @get()
    async def get_all_products(
        self,
        db_session: AsyncSession,
        product_service: ProductService,
        page: int = Parameter(default=1, ge=1),
        count: int = Parameter(default=10, ge=1, le=100),
    ) -> List[ProductResponse]:
        """
        Получить список всей продукции

        Args:
            db_session: Сессия базы данных (dependency injection)
            product_service: Сервис для работы с продукцией (dependency injection)
            page: Номер страницы
            count: Количество записей на странице

        Returns:
            Список продукции
        """
        products = await product_service.get_all(db_session, count, page)
        return [ProductResponse.model_validate(product) for product in products]
