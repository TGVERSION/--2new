import pytest
from unittest.mock import Mock, AsyncMock
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from app.services.product_service import ProductService
from app.repositories.product_repository import ProductRepository


class TestProductService:
    """Тесты для ProductService"""

    @pytest.mark.asyncio
    async def test_get_by_id_success(self):
        """Тест успешного получения продукта по ID"""
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_product_repo.get_by_id.return_value = Mock(
            id="1", name="Test Product", price=100.0, stock_quantity=10
        )
        
        product_service = ProductService(product_repository=mock_product_repo)
        
        result = await product_service.get_by_id(None, "1")
        
        assert result is not None
        assert result.id == "1"
        mock_product_repo.get_by_id.assert_called_once_with(None, "1")

    @pytest.mark.asyncio
    async def test_create_product_success(self):
        """Тест успешного создания продукта"""
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_product = Mock()
        mock_product.id = "1"
        mock_product.name = "Test Product"
        mock_product.price = 100.0
        mock_product.stock_quantity = 10
        mock_product_repo.create.return_value = mock_product
        
        product_service = ProductService(product_repository=mock_product_repo)
        
        from app.schemas.product import ProductCreate
        product_data = ProductCreate(
            name="Test Product",
            price=100.0,
            stock_quantity=10
        )
        
        result = await product_service.create(None, product_data)
        
        assert result is not None
        # Проверяем, что результат соответствует моку
        assert result.id == "1"
        assert result.name == "Test Product"
        mock_product_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_product_not_found(self):
        """Тест обновления несуществующего продукта"""
        mock_product_repo = AsyncMock(spec=ProductRepository)
        mock_product_repo.update.return_value = None
        
        product_service = ProductService(product_repository=mock_product_repo)
        
        from app.schemas.product import ProductUpdate
        product_data = ProductUpdate(price=150.0)
        
        with pytest.raises(ValueError, match="not found"):
            await product_service.update(None, "999", product_data)

