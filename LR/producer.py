"""Продюсер данных для RabbitMQ"""
import json
import time
import pika
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker
from models import User, Address, Product


def get_user_and_address_ids():
    """Получить user_id и delivery_address_id из базы данных"""
    engine = create_engine("sqlite:///lab2.db", echo=False)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        # Получаем первого пользователя и его адрес
        user = session.execute(select(User)).scalars().first()
        if not user:
            raise ValueError("В базе данных нет пользователей. Запустите seed_data.py сначала.")
        
        address = session.execute(
            select(Address).where(Address.user_id == user.id)
        ).scalars().first()
        
        if not address:
            raise ValueError("В базе данных нет адресов. Запустите seed_data.py сначала.")
        
        return user.id, address.id


def send_message(queue_name: str, message: dict):
    """Отправить сообщение в очередь RabbitMQ"""
    # Создание подключения
    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host='localhost', port=5672, virtual_host="local")
    )
    channel = connection.channel()
    
    # Отправка сообщения
    channel.basic_publish(
        exchange='',
        routing_key=queue_name,
        body=json.dumps(message),
    )
    
    print(f"Отправлено сообщение в очередь '{queue_name}': {message}")
    
    connection.close()


def create_products():
    """Создать 5 продукций через RabbitMQ"""
    products_data = [
        {
            "operation": "create",
            "name": "Ноутбук",
            "description": "Высокопроизводительный ноутбук",
            "price": 999.99,
            "stock_quantity": 10
        },
        {
            "operation": "create",
            "name": "Смартфон",
            "description": "Последняя модель смартфона",
            "price": 699.99,
            "stock_quantity": 15
        },
        {
            "operation": "create",
            "name": "Наушники",
            "description": "Беспроводные наушники",
            "price": 199.99,
            "stock_quantity": 20
        },
        {
            "operation": "create",
            "name": "Планшет",
            "description": "10-дюймовый планшет",
            "price": 449.99,
            "stock_quantity": 8
        },
        {
            "operation": "create",
            "name": "Умные часы",
            "description": "Фитнес-умные часы",
            "price": 299.99,
            "stock_quantity": 12
        }
    ]
    
    for product_data in products_data:
        send_message("product", product_data)


def create_orders():
    """Создать 3 заказа через RabbitMQ"""
    try:
        user_id, address_id = get_user_and_address_ids()
    except ValueError as e:
        print(f"Ошибка: {e}")
        return
    
    # Получаем список продуктов из базы для создания заказов
    engine = create_engine("sqlite:///lab2.db", echo=False)
    Session = sessionmaker(bind=engine)
    
    with Session() as session:
        products = session.execute(select(Product)).scalars().all()
        
        if len(products) < 2:
            print("Ошибка: В базе данных недостаточно продуктов для создания заказов")
            return
        
        orders_data = [
            {
                "operation": "create",
                "user_id": user_id,
                "delivery_address_id": address_id,
                "items": [
                    {
                        "product_id": products[0].id,
                        "quantity": 1
                    },
                    {
                        "product_id": products[2].id,
                        "quantity": 2
                    }
                ]
            },
            {
                "operation": "create",
                "user_id": user_id,
                "delivery_address_id": address_id,
                "items": [
                    {
                        "product_id": products[1].id,
                        "quantity": 1
                    },
                    {
                        "product_id": products[4].id if len(products) > 4 else products[0].id,
                        "quantity": 1
                    }
                ]
            },
            {
                "operation": "create",
                "user_id": user_id,
                "delivery_address_id": address_id,
                "items": [
                    {
                        "product_id": products[3].id if len(products) > 3 else products[0].id,
                        "quantity": 1
                    }
                ]
            }
        ]
        
        for order_data in orders_data:
            send_message("order", order_data)


def main():
    """Основная функция для отправки данных"""
    print("=== Создание продукции ===")
    create_products()
    
    # Ждем, пока обработчики RabbitMQ обработают сообщения о создании продукции
    print("\nОжидание обработки сообщений о продукции (5 секунд)...")
    time.sleep(5)
    
    print("\n=== Создание заказов ===")
    create_orders()
    
    print("\n=== Готово ===")


if __name__ == "__main__":
    main()

