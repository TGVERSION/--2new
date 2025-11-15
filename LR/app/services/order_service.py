from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
import sys
from pathlib import Path

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Order
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import OrderCreate, OrderUpdate


class OrderService:
    """Сервисный слой для работы с заказами"""

    def __init__(
        self, 
        order_repository: OrderRepository,
        product_repository: ProductRepository,
        user_repository: UserRepository
    ):
        """
        Инициализация сервиса
        
        Args:
            order_repository: Репозиторий для работы с заказами
            product_repository: Репозиторий для работы с продуктами
            user_repository: Репозиторий для работы с пользователями
        """
        self.order_repository = order_repository
        self.product_repository = product_repository
        self.user_repository = user_repository

    async def get_by_id(self, session: AsyncSession, order_id: str) -> Optional[Order]:
        """
        Получить заказ по ID
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)
            
        Returns:
            Order или None, если заказ не найден
        """
        return await self.order_repository.get_by_id(session, order_id)

    async def get_all(
        self, 
        session: AsyncSession,
        count: int = 100, 
        page: int = 1
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
        return await self.order_repository.get_all(session, count, page)

    async def create_order(
        self, 
        session: AsyncSession,
        order_data: dict
    ) -> Order:
        """
        Создать новый заказ
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            order_data: Данные для создания заказа (dict с user_id и items)
            
        Returns:
            Созданный заказ
            
        Raises:
            ValueError: Если пользователь не найден, продукт не найден или недостаточно товара на складе
        """
        from app.schemas.order import OrderCreate, OrderItemCreate
        
        # Преобразуем dict в OrderCreate
        order_create = OrderCreate(
            user_id=order_data["user_id"],
            delivery_address_id=order_data.get("delivery_address_id", ""),
            items=[OrderItemCreate(**item) for item in order_data["items"]]
        )
        
        # Проверяем существование пользователя
        user = await self.user_repository.get_by_id(session, order_create.user_id)
        if not user:
            raise ValueError(f"User with id {order_create.user_id} not found")
        
        # Проверяем продукты и рассчитываем общую сумму
        total_amount = 0.0
        for item in order_create.items:
            product = await self.product_repository.get_by_id(session, item.product_id)
            if not product:
                raise ValueError(f"Product with id {item.product_id} not found")
            
            # Проверяем количество товара на складе
            if product.stock_quantity < item.quantity:
                raise ValueError("Insufficient stock")
            
            total_amount += product.price * item.quantity
        
        # Создаем заказ
        order = await self.order_repository.create(session, order_create, total_amount)
        
        # Обновляем количество товара на складе
        for item in order_create.items:
            product = await self.product_repository.get_by_id(session, item.product_id)
            if product:
                product.stock_quantity -= item.quantity
        
        # Сохраняем изменения один раз после всех обновлений
        if session:
            await session.commit()
        
        return order

    async def update(
        self, 
        session: AsyncSession,
        order_id: str, 
        order_data: OrderUpdate
    ) -> Order:
        """
        Обновить заказ
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)
            order_data: Данные для обновления заказа
            
        Returns:
            Обновленный заказ
            
        Raises:
            ValueError: Если заказ не найден
        """
        updated_order = await self.order_repository.update(session, order_id, order_data)
        if updated_order is None:
            raise ValueError(f"Order with id {order_id} not found")
        return updated_order

    async def delete(self, session: AsyncSession, order_id: str) -> None:
        """
        Удалить заказ
        
        Args:
            session: Асинхронная сессия SQLAlchemy
            order_id: ID заказа (UUID в виде строки)
        """
        await self.order_repository.delete(session, order_id)

