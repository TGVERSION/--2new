import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from models import Product
from app.repositories.product_repository import ProductRepository


class TestProductRepository:
    """Тесты для ProductRepository"""

    @pytest.mark.asyncio
    async def test_create_product(self, product_repository: ProductRepository, session):
        """Тест создания продукта в репозитории"""
        product_data = {
            "name": "Test Product",
            "description": "Test description",
            "price": 100.0,
            "stock_quantity": 10
        }
        
        product = await product_repository.create(session, **product_data)
        
        assert product.id is not None
        assert product.name == "Test Product"
        assert product.price == 100.0
        assert product.stock_quantity == 10

    @pytest.mark.asyncio
    async def test_get_product_by_id(self, product_repository: ProductRepository, session):
        """Тест получения продукта по ID"""
        product = await product_repository.create(
            session,
            name="Get Product",
            description="Test",
            price=50.0,
            stock_quantity=5
        )
        
        found_product = await product_repository.get_by_id(session, product.id)
        
        assert found_product is not None
        assert found_product.id == product.id
        assert found_product.name == "Get Product"

    @pytest.mark.asyncio
    async def test_update_product(self, product_repository: ProductRepository, session):
        """Тест обновления продукта"""
        product = await product_repository.create(
            session,
            name="Original Product",
            description="Original",
            price=100.0,
            stock_quantity=10
        )
        
        updated_product = await product_repository.update(session, product.id, price=150.0)
        
        assert updated_product.name == "Original Product"
        assert updated_product.price == 150.0
        assert updated_product.stock_quantity == 10  # не изменилось

    @pytest.mark.asyncio
    async def test_delete_product(self, product_repository: ProductRepository, session):
        """Тест удаления продукта"""
        product = await product_repository.create(
            session,
            name="Delete Product",
            description="Test",
            price=75.0,
            stock_quantity=3
        )
        product_id = product.id
        
        await product_repository.delete(session, product_id)
        
        deleted_product = await product_repository.get_by_id(session, product_id)
        assert deleted_product is None

    @pytest.mark.asyncio
    async def test_get_all_products(self, product_repository: ProductRepository, session):
        """Тест получения списка продуктов"""
        await product_repository.create(
            session,
            name="Product 1",
            description="First",
            price=10.0,
            stock_quantity=5
        )
        await product_repository.create(
            session,
            name="Product 2",
            description="Second",
            price=20.0,
            stock_quantity=8
        )
        
        products = await product_repository.get_all(session, count=10, page=1)
        
        assert len(products) >= 2

