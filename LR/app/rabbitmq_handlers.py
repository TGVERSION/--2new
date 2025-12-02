"""Обработчики сообщений RabbitMQ для заказов и продукции"""

import sys
from pathlib import Path

from faststream import FastStream  # pylint: disable=import-error
from faststream.rabbit import RabbitBroker  # pylint: disable=import-error
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

# Добавляем путь к корневой папке проекта для импорта
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Настройка базы данных
import os

from app.repositories.order_repository import OrderRepository
from app.repositories.product_repository import ProductRepository
from app.repositories.user_repository import UserRepository
from app.schemas.order import OrderCreate, OrderUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.order_service import OrderService
from app.services.product_service import ProductService

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./lab2.db")
engine = create_async_engine(DATABASE_URL, echo=False)
async_session_factory = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


# Инициализация брокера RabbitMQ
broker = RabbitBroker("amqp://guest:guest@localhost:5672/local")
app = FastStream(broker)

# Инициализация репозиториев и сервисов
order_repository = OrderRepository()
product_repository = ProductRepository()
user_repository = UserRepository()
order_service = OrderService(order_repository, product_repository, user_repository)
product_service = ProductService(product_repository)


@broker.subscriber("order")
async def subscribe_order(message: dict):

    async with async_session_factory() as session:
        try:
            operation = message.get("operation")

            if operation == "create":
                # Создание нового заказа
                order_data = {
                    "user_id": message.get("user_id"),
                    "delivery_address_id": message.get("delivery_address_id"),
                    "items": message.get("items", []),
                }

                # Проверяем наличие всех необходимых полей
                if not order_data["user_id"] or not order_data["delivery_address_id"]:
                    print(f"ERROR: Недостаточно данных для создания заказа: {message}")
                    await session.rollback()
                    return

                # Проверяем наличие товаров на складе перед созданием заказа
                for item in order_data["items"]:
                    product = await product_repository.get_by_id(
                        session, item.get("product_id")
                    )
                    if not product:
                        print(f"ERROR: Продукт с id {item.get('product_id')} не найден")
                        await session.rollback()
                        return
                    if product.stock_quantity < item.get("quantity", 0):
                        print(
                            f"ERROR: Недостаточно товара на складе для продукта {product.name}"
                        )
                        await session.rollback()
                        return

                order = await order_service.create_order(session, order_data)
                print(f"SUCCESS: Создан заказ с id {order.id}")

            elif operation == "update":
                # Обновление заказа
                order_id = message.get("order_id")
                if not order_id:
                    print(f"ERROR: Не указан order_id для обновления: {message}")
                    await session.rollback()
                    return

                update_data = OrderUpdate(
                    delivery_address_id=message.get("delivery_address_id")
                )
                order = await order_service.update(session, order_id, update_data)
                print(f"SUCCESS: Обновлен заказ с id {order.id}")

            else:
                print(
                    f"ERROR: Неизвестная операция '{operation}' для заказа: {message}"
                )
                await session.rollback()

        except (ValueError, SQLAlchemyError) as e:
            print(f"ERROR: Ошибка при обработке заказа: {e}")
            await session.rollback()
            import traceback

            traceback.print_exc()
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Ловим все остальные исключения для логирования
            print(f"ERROR: Неожиданная ошибка при обработке заказа: {e}")
            await session.rollback()
            import traceback

            traceback.print_exc()


@broker.subscriber("product")
async def subscribe_product(message: dict):

    async with async_session_factory() as session:
        try:
            operation = message.get("operation")

            if operation == "create":
                # Создание новой продукции
                product_data = ProductCreate(
                    name=message.get("name"),
                    description=message.get("description"),
                    price=message.get("price"),
                    stock_quantity=message.get("stock_quantity", 0),
                )

                if not product_data.name or product_data.price is None:
                    print(
                        f"ERROR: Недостаточно данных для создания продукции: {message}"
                    )
                    await session.rollback()
                    return

                product = await product_service.create(session, product_data)
                print(
                    f"SUCCESS: Создана продукция с id {product.id}, название: {product.name}"
                )

            elif operation == "update":
                # Обновление продукции
                product_id = message.get("product_id")
                if not product_id:
                    print(f"ERROR: Не указан product_id для обновления: {message}")
                    await session.rollback()
                    return

                update_data = ProductUpdate(
                    name=message.get("name"),
                    description=message.get("description"),
                    price=message.get("price"),
                    stock_quantity=message.get("stock_quantity"),
                )
                product = await product_service.update(session, product_id, update_data)
                print(f"SUCCESS: Обновлена продукция с id {product.id}")

            elif operation == "mark_out_of_stock":
                # Отметить продукцию как закончившуюся на складе
                product_id = message.get("product_id")
                if not product_id:
                    print(f"ERROR: Не указан product_id: {message}")
                    await session.rollback()
                    return

                update_data = ProductUpdate(stock_quantity=0)
                product = await product_service.update(session, product_id, update_data)
                print(
                    f"SUCCESS: Продукция с id {product.id} отмечена как закончившаяся на складе"
                )

            else:
                print(
                    f"ERROR: Неизвестная операция '{operation}' для продукции: {message}"
                )
                await session.rollback()

        except (ValueError, SQLAlchemyError) as e:
            print(f"ERROR: Ошибка при обработке продукции: {e}")
            await session.rollback()
            import traceback

            traceback.print_exc()
        except Exception as e:  # pylint: disable=broad-exception-caught
            # Ловим все остальные исключения для логирования
            print(f"ERROR: Неожиданная ошибка при обработке продукции: {e}")
            await session.rollback()
            import traceback

            traceback.print_exc()


if __name__ == "__main__":
    import asyncio

    async def main():
        await app.run()

    asyncio.run(main())
