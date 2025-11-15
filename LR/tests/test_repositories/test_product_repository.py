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

    @pytest.mark.asyncio
    async def test_get_all_products_pagination(self, product_repository: ProductRepository, session):
        """Тест пагинации товаров - проверка параметров count и page"""
        # Создаем 15 товаров для тестирования пагинации
        created_products = []
        for i in range(15):
            product = await product_repository.create(
                session,
                name=f"Product {i+1}",
                description=f"Test product {i+1}",
                price=float(10 * (i+1)),
                stock_quantity=i+1
            )
            created_products.append(product)
        
        # Тест 1: Первая страница с 5 товарами
        products_page1 = await product_repository.get_all(session, count=5, page=1)
        assert len(products_page1) == 5, "Первая страница должна содержать 5 товаров"
        assert products_page1[0].name == "Product 1", "Первый товар должен быть первым на странице"
        assert products_page1[4].name == "Product 5", "Пятый товар должен быть последним на первой странице"
        
        # Тест 2: Вторая страница с 5 товарами
        products_page2 = await product_repository.get_all(session, count=5, page=2)
        assert len(products_page2) == 5, "Вторая страница должна содержать 5 товаров"
        assert products_page2[0].name == "Product 6", "Первый товар на второй странице должен быть 6-м"
        assert products_page2[4].name == "Product 10", "Последний товар на второй странице должен быть 10-м"
        
        # Тест 3: Третья страница с 5 товарами (должна содержать оставшиеся)
        products_page3 = await product_repository.get_all(session, count=5, page=3)
        assert len(products_page3) == 5, "Третья страница должна содержать 5 товаров"
        assert products_page3[0].name == "Product 11", "Первый товар на третьей странице должен быть 11-м"
        
        # Тест 4: Четвертая страница (должна быть пустой или содержать остаток)
        products_page4 = await product_repository.get_all(session, count=5, page=4)
        assert len(products_page4) == 0, "Четвертая страница должна быть пустой (товаров не осталось)"
        
        # Тест 5: Страница с большим count (больше чем товаров)
        products_all = await product_repository.get_all(session, count=100, page=1)
        assert len(products_all) >= 15, "При большом count должны вернуться все товары"
        
        # Тест 6: Пагинация с count=10, page=1
        products_count10 = await product_repository.get_all(session, count=10, page=1)
        assert len(products_count10) == 10, "При count=10 должно вернуться 10 товаров"
        
        # Тест 7: Пагинация с count=10, page=2
        products_count10_page2 = await product_repository.get_all(session, count=10, page=2)
        assert len(products_count10_page2) == 5, "На второй странице должно быть 5 товаров (остаток от 15)"
        
        # Тест 8: Граничный случай - count=1, page=1 (получение одного товара)
        products_single = await product_repository.get_all(session, count=1, page=1)
        assert len(products_single) == 1, "При count=1 должен вернуться 1 товар"
        
        # Тест 9: Проверка корректности offset - каждая страница должна содержать разные товары
        page1_ids = {p.id for p in products_page1}
        page2_ids = {p.id for p in products_page2}
        assert page1_ids.isdisjoint(page2_ids), "Товары на разных страницах не должны повторяться"
        
        # Тест 10: Проверка сортировки - товары должны быть в порядке создания (проверяем по именам)
        # Имена уже проверены выше, поэтому дополнительная проверка не требуется
        # Сортировка проверена через сравнение имен продуктов на разных страницах

