"""Контроллер для управления заказами"""

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

from app.schemas.order import OrderResponse
from app.services.order_service import OrderService


class OrderController(Controller):
    """Контроллер для управления заказами"""

    path = "/orders"
    tags = ["orders"]

    @get("/{order_id:str}")
    async def get_order_by_id(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        order_id: str,
    ) -> OrderResponse:
        """
        Получить заказ по ID

        Args:
            order_id: ID заказа (UUID в формате строки)
            db_session: Сессия базы данных (dependency injection)
            order_service: Сервис для работы с заказами (dependency injection)

        Returns:
            Данные заказа

        Raises:
            NotFoundException: Если заказ не найден
        """
        order = await order_service.get_by_id(db_session, order_id)
        if not order:
            raise NotFoundException(detail=f"Order with ID {order_id} not found")
        return OrderResponse.model_validate(order)

    @get()
    async def get_all_orders(
        self,
        db_session: AsyncSession,
        order_service: OrderService,
        page: int = Parameter(default=1, ge=1),
        count: int = Parameter(default=10, ge=1, le=100),
    ) -> List[OrderResponse]:
        """
        Получить список всех заказов

        Args:
            db_session: Сессия базы данных (dependency injection)
            order_service: Сервис для работы с заказами (dependency injection)
            page: Номер страницы
            count: Количество записей на странице

        Returns:
            Список заказов
        """
        orders = await order_service.get_all(db_session, count, page)
        return [OrderResponse.model_validate(order) for order in orders]
