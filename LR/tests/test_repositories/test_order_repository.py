import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Order, OrderItem, User, Address, Product
from app.repositories.order_repository import OrderRepository
from app.repositories.user_repository import UserRepository
from app.repositories.product_repository import ProductRepository
from app.schemas.order import OrderCreate, OrderItemCreate


class TestOrderRepository:
    """Тесты для OrderRepository"""

    @pytest.mark.asyncio
    async def test_create_order(
        self, 
        order_repository: OrderRepository, 
        user_repository: UserRepository,
        product_repository: ProductRepository,
        session
    ):
        """Тест создания заказа с несколькими продуктами"""
        # Создаем пользователя
        user = await user_repository.create(
            session,
            email="order@example.com",
            username="order_user",
            description="Order user"
        )
        
        # Создаем адрес (упрощенная версия, в реальности нужен AddressRepository)
        from models import Address
        address = Address(
            user_id=user.id,
            street="Test Street",
            city="Test City",
            country="Test Country"
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        
        # Создаем продукты
        product1 = await product_repository.create(
            session,
            name="Product 1",
            price=100.0,
            stock_quantity=10
        )
        product2 = await product_repository.create(
            session,
            name="Product 2",
            price=200.0,
            stock_quantity=5
        )
        
        # Создаем заказ с несколькими продуктами
        order_data = OrderCreate(
            user_id=user.id,
            delivery_address_id=address.id,
            items=[
                OrderItemCreate(product_id=product1.id, quantity=2),
                OrderItemCreate(product_id=product2.id, quantity=1)
            ]
        )
        
        order = await order_repository.create(session, order_data, total_amount=400.0)
        
        # Загружаем order_items
        await session.refresh(order, ["order_items"])
        
        assert order.id is not None
        assert order.user_id == user.id
        assert len(order.order_items) == 2

    @pytest.mark.asyncio
    async def test_get_order_by_id(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        session
    ):
        """Тест получения заказа по ID"""
        # Создаем необходимые данные
        user = await user_repository.create(
            session,
            email="get@example.com",
            username="get_user",
            description="Get user"
        )
        
        from models import Address
        address = Address(
            user_id=user.id,
            street="Test Street",
            city="Test City",
            country="Test Country"
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        
        product = await product_repository.create(
            session,
            name="Test Product",
            price=50.0,
            stock_quantity=10
        )
        
        order_data = OrderCreate(
            user_id=user.id,
            delivery_address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        
        order = await order_repository.create(session, order_data, total_amount=50.0)
        
        found_order = await order_repository.get_by_id(session, order.id)
        
        assert found_order is not None
        assert found_order.id == order.id

    @pytest.mark.asyncio
    async def test_update_order(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        session
    ):
        """Тест обновления заказа"""
        user = await user_repository.create(
            session,
            email="update@example.com",
            username="update_user",
            description="Update user"
        )
        
        from models import Address
        address1 = Address(
            user_id=user.id,
            street="Address 1",
            city="City 1",
            country="Country 1"
        )
        address2 = Address(
            user_id=user.id,
            street="Address 2",
            city="City 2",
            country="Country 2"
        )
        session.add(address1)
        session.add(address2)
        await session.commit()
        await session.refresh(address1)
        await session.refresh(address2)
        
        product = await product_repository.create(
            session,
            name="Test Product",
            price=100.0,
            stock_quantity=10
        )
        
        order_data = OrderCreate(
            user_id=user.id,
            delivery_address_id=address1.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        
        order = await order_repository.create(session, order_data, total_amount=100.0)
        
        from app.schemas.order import OrderUpdate
        updated_order = await order_repository.update(
            session, 
            order.id, 
            OrderUpdate(delivery_address_id=address2.id)
        )
        
        assert updated_order.delivery_address_id == address2.id

    @pytest.mark.asyncio
    async def test_delete_order(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        session
    ):
        """Тест удаления заказа"""
        user = await user_repository.create(
            session,
            email="delete@example.com",
            username="delete_user",
            description="Delete user"
        )
        
        from models import Address
        address = Address(
            user_id=user.id,
            street="Test Street",
            city="Test City",
            country="Test Country"
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        
        product = await product_repository.create(
            session,
            name="Test Product",
            price=75.0,
            stock_quantity=5
        )
        
        order_data = OrderCreate(
            user_id=user.id,
            delivery_address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        
        order = await order_repository.create(session, order_data, total_amount=75.0)
        order_id = order.id
        
        await order_repository.delete(session, order_id)
        
        deleted_order = await order_repository.get_by_id(session, order_id)
        assert deleted_order is None

    @pytest.mark.asyncio
    async def test_get_all_orders(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
        session
    ):
        """Тест получения списка заказов"""
        user = await user_repository.create(
            session,
            email="list@example.com",
            username="list_user",
            description="List user"
        )
        
        from models import Address
        address = Address(
            user_id=user.id,
            street="Test Street",
            city="Test City",
            country="Test Country"
        )
        session.add(address)
        await session.commit()
        await session.refresh(address)
        
        product = await product_repository.create(
            session,
            name="Test Product",
            price=50.0,
            stock_quantity=10
        )
        
        order_data1 = OrderCreate(
            user_id=user.id,
            delivery_address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=1)]
        )
        order_data2 = OrderCreate(
            user_id=user.id,
            delivery_address_id=address.id,
            items=[OrderItemCreate(product_id=product.id, quantity=2)]
        )
        
        await order_repository.create(session, order_data1, total_amount=50.0)
        await order_repository.create(session, order_data2, total_amount=100.0)
        
        orders = await order_repository.get_all(session, count=10, page=1)
        
        assert len(orders) >= 2

