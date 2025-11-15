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

