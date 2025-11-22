import sys
from pathlib import Path
from typing import List, Optional

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

# Добавляем путь к корневой папке проекта для импорта моделей
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.schemas.order import OrderCreate, OrderUpdate
from models import Order, OrderItem


class OrderRepository:
    """Репозиторий для работы с заказами"""

    async def get_by_id(self, session: AsyncSession, order_id: str) -> Optional[Order]:
        """
        Получить заказ по ID

        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)

        Returns:
            Order или None, если заказ не найден
        """
        result = await session.execute(select(Order).where(Order.id == order_id))
        return result.scalar_one_or_none()

    async def get_all(
        self, session: AsyncSession, count: int = 100, page: int = 1
    ) -> List[Order]:
        """
        Получить список всех заказов с пагинацией

        Args:
            session: Асинхронная сессия SQLAlchemy
            count: Количество записей на странице
            page: Номер страницы (начиная с 1)

        Returns:
            Список заказов
        """
        offset = (page - 1) * count if page > 0 else 0
        query = select(Order).offset(offset).limit(count)
        result = await session.execute(query)
        return list(result.scalars().all())

    async def create(
        self, session: AsyncSession, order_data: OrderCreate, total_amount: float
    ) -> Order:
        """
        Создать новый заказ

        Args:
            session: Асинхронная сессия SQLAlchemy
            order_data: Данные для создания заказа
            total_amount: Общая сумма заказа

        Returns:
            Созданный заказ
        """
        order = Order(
            user_id=order_data.user_id,
            delivery_address_id=order_data.delivery_address_id,
        )
        session.add(order)
        await session.flush()  # Получаем ID заказа

        # Создаем элементы заказа
        for item_data in order_data.items:
            order_item = OrderItem(
                order_id=order.id,
                product_id=item_data.product_id,
                quantity=item_data.quantity,
            )
            session.add(order_item)

        await session.commit()
        await session.refresh(order)
        return order

    async def update(
        self, session: AsyncSession, order_id: str, order_data: OrderUpdate
    ) -> Optional[Order]:
        """
        Обновить заказ

        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)
            order_data: Данные для обновления заказа

        Returns:
            Обновленный заказ или None, если заказ не найден
        """
        # Получаем заказ
        order = await self.get_by_id(session, order_id)
        if not order:
            return None

        # Обновляем только переданные поля
        update_data = order_data.model_dump(exclude_unset=True)
        if not update_data:
            return order

        # Обновляем поля
        for field, value in update_data.items():
            setattr(order, field, value)

        await session.commit()
        await session.refresh(order)
        return order

    async def delete(self, session: AsyncSession, order_id: str) -> None:
        """
        Удалить заказ

        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)
        """
        await session.execute(delete(Order).where(Order.id == order_id))
        await session.commit()
