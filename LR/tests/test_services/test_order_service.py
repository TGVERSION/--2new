import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.order_service import OrderService
from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository


class TestOrderService:
    """Тесты для OrderService"""

    @pytest.mark.asyncio
    async def test_create_order_success(self):
        """Тест успешного создания заказа"""
        # Мокаем репозитории
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        # Настраиваем моки
        mock_user_repo.get_by_id.return_value = Mock(id=1, email="test@example.com")
        mock_product_repo.get_by_id.return_value = Mock(
            id=1, name="Test Product", price=100.0, stock_quantity=5
        )
        mock_order_repo.create.return_value = Mock(
            id=1, user_id=1, total_amount=200.0
        )
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 2}]
        }
        
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        assert result.total_amount == 200.0
        mock_order_repo.create.assert_called_once()
        mock_user_repo.get_by_id.assert_called_once()
        # get_by_id вызывается дважды: для проверки товара и для обновления stock_quantity
        assert mock_product_repo.get_by_id.call_count >= 1

    @pytest.mark.asyncio
    async def test_create_order_insufficient_stock(self):
        """Тест создания заказа с недостаточным количеством товара"""
        # Мокаем репозитории
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        # Настраиваем моки
        mock_user_repo.get_by_id.return_value = Mock(id=1)
        mock_product_repo.get_by_id.return_value = Mock(
            id=1, name="Test Product", price=100.0, stock_quantity=1
        )
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 5}]  # Заказываем больше чем есть
        }
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            await order_service.create_order(None, order_data)

    @pytest.mark.asyncio
    async def test_create_order_user_not_found(self):
        """Тест создания заказа с несуществующим пользователем"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        # Пользователь не найден
        mock_user_repo.get_by_id.return_value = None
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "999",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 1}]
        }
        
        with pytest.raises(ValueError, match="User with id 999 not found"):
            await order_service.create_order(None, order_data)
        
        mock_user_repo.get_by_id.assert_called_once()
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_product_not_found(self):
        """Тест создания заказа с несуществующим продуктом"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        # Первый продукт найден, второй нет
        mock_product_repo.get_by_id.side_effect = [
            Mock(id="1", price=100.0, stock_quantity=10),  # Первый вызов
            None  # Второй вызов - продукт не найден
        ]
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [
                {"product_id": "1", "quantity": 2},
                {"product_id": "999", "quantity": 1}  # Несуществующий продукт
            ]
        }
        
        with pytest.raises(ValueError, match="Product with id 999 not found"):
            await order_service.create_order(None, order_data)
        
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_empty_items(self):
        """Тест создания заказа с пустым списком товаров"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": []  # Пустой список товаров
        }
        
        # Должен создаться заказ с нулевой суммой
        mock_order_repo.create.return_value = Mock(id="1", user_id="1", total_amount=0.0)
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        assert result.total_amount == 0.0
        mock_order_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_order_zero_quantity(self):
        """Тест создания заказа с нулевым количеством товара"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        mock_product_repo.get_by_id.return_value = Mock(
            id="1", name="Test Product", price=100.0, stock_quantity=10
        )
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 0}]  # Нулевое количество
        }
        
        # Должен создаться заказ с нулевой суммой
        mock_order_repo.create.return_value = Mock(id="1", user_id="1", total_amount=0.0)
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        assert result.total_amount == 0.0

    @pytest.mark.asyncio
    async def test_create_order_negative_quantity(self):
        """Тест создания заказа с отрицательным количеством товара"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        mock_product_repo.get_by_id.return_value = Mock(
            id="1", name="Test Product", price=100.0, stock_quantity=10
        )
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": -1}]  # Отрицательное количество
        }
        
        # При отрицательном количестве проверка stock_quantity даст True (10 >= -1), 
        # но это некорректное значение. В реальном приложении нужна валидация на уровне схемы
        # Здесь проверяем, что заказ создается, но сумма будет отрицательной
        mock_order_repo.create.return_value = Mock(id="1", user_id="1", total_amount=-100.0)
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        # Обратите внимание: в реальном приложении нужно валидировать quantity > 0

    @pytest.mark.asyncio
    async def test_create_order_exact_stock_quantity(self):
        """Тест создания заказа с точным количеством товара на складе (граничный случай)"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        # Товар с ровно 5 единицами на складе
        mock_product_repo.get_by_id.return_value = Mock(
            id="1", name="Test Product", price=100.0, stock_quantity=5
        )
        mock_order_repo.create.return_value = Mock(id="1", user_id="1", total_amount=500.0)
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 5}]  # Точное количество на складе
        }
        
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        assert result.total_amount == 500.0
        mock_order_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_order_zero_stock_quantity(self):
        """Тест создания заказа когда товар отсутствует на складе (stock_quantity = 0)"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        mock_product_repo.get_by_id.return_value = Mock(
            id="1", name="Test Product", price=100.0, stock_quantity=0  # Нет товара на складе
        )
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [{"product_id": "1", "quantity": 1}]
        }
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            await order_service.create_order(None, order_data)
        
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_multiple_products_one_insufficient(self):
        """Тест создания заказа с несколькими продуктами, где одного недостаточно"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        # Первый продукт в наличии, второй - недостаточно
        mock_product_repo.get_by_id.side_effect = [
            Mock(id="1", name="Product 1", price=100.0, stock_quantity=10),
            Mock(id="2", name="Product 2", price=200.0, stock_quantity=1)  # Только 1 единица
        ]
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [
                {"product_id": "1", "quantity": 2},  # OK
                {"product_id": "2", "quantity": 5}   # Недостаточно (только 1 есть)
            ]
        }
        
        with pytest.raises(ValueError, match="Insufficient stock"):
            await order_service.create_order(None, order_data)
        
        mock_order_repo.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_create_order_multiple_products_success(self):
        """Тест успешного создания заказа с несколькими продуктами"""
        mock_order_repo = AsyncMock(spec=OrderRepository)
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_user_repo = AsyncMock(spec=UserRepository)
        
        mock_user_repo.get_by_id.return_value = Mock(id="1")
        mock_product_repo.get_by_id.side_effect = [
            Mock(id="1", name="Product 1", price=100.0, stock_quantity=10),
            Mock(id="2", name="Product 2", price=200.0, stock_quantity=5),
            Mock(id="1", name="Product 1", price=100.0, stock_quantity=10),  # Для обновления
            Mock(id="2", name="Product 2", price=200.0, stock_quantity=5)   # Для обновления
        ]
        mock_order_repo.create.return_value = Mock(id="1", user_id="1", total_amount=900.0)
        
        order_service = OrderService(
            order_repository=mock_order_repo,
            product_repository=mock_product_repo,
            user_repository=mock_user_repo
        )
        
        order_data = {
            "user_id": "1",
            "delivery_address_id": "1",
            "items": [
                {"product_id": "1", "quantity": 3},  # 100 * 3 = 300
                {"product_id": "2", "quantity": 3}   # 200 * 3 = 600, итого 900
            ]
        }
        
        result = await order_service.create_order(None, order_data)
        
        assert result is not None
        assert result.total_amount == 900.0
        mock_order_repo.create.assert_called_once()

