from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker, selectinload
from models import User, Address, Product, Order, OrderItem

# Подключение к базе данных SQLite
engine = create_engine("sqlite:///lab2.db", echo=True)
# Создаем фабрику сессий для работы с базой данных
Session = sessionmaker(bind=engine)


def add_or_update_data():
    """Добавляет или обновляет данные в базе данных"""
    with Session() as session:
        # Проверяем, есть ли уже пользователи в базе
        existing_users = session.execute(select(User)).scalars().all()

        if existing_users:
            print("Updating existing data...")
            # Обновляем описания существующих пользователей
            descriptions = [
                "Regular customer interested in electronics",
                "Premium customer with frequent purchases",
                "New customer exploring our products",
                "Business customer with bulk orders",
                "VIP customer with special preferences"
            ]
            for i, user in enumerate(existing_users[:5]):
                user.description = descriptions[i]
            session.commit()
            users = existing_users
        else:
            print("Creating new data...")
            # Создаем новых пользователей
            users_data = [
                {"username": "john_doe", "email": "john@example.com",
                    "description": "Regular customer"},
                {"username": "jane_smith", "email": "jane@example.com",
                    "description": "Premium customer"},
                {"username": "bob_wilson", "email": "bob@example.com",
                    "description": "New customer"},
                {"username": "alice_brown", "email": "alice@example.com",
                    "description": "Business customer"},
                {"username": "charlie_davis", "email": "charlie@example.com",
                    "description": "VIP customer"}
            ]

            users = []
            for user_data in users_data:
                user = User(
                    username=user_data["username"],
                    email=user_data["email"],
                    description=user_data["description"]
                )
                users.append(user)
                session.add(user)
            session.commit()

        # Добавляем адреса, если их нет
        existing_addresses = session.execute(select(Address)).scalars().all()
        if not existing_addresses:
            addresses_data = [
                {"user": users[0], "street": "123 Main St", "city": "New York",
                    "state": "NY", "zip_code": "10001", "country": "USA", "is_primary": True},
                {"user": users[1], "street": "456 Oak Ave", "city": "Los Angeles",
                    "state": "CA", "zip_code": "90210", "country": "USA", "is_primary": True},
                {"user": users[2], "street": "789 Pine Rd", "city": "Chicago",
                    "state": "IL", "zip_code": "60601", "country": "USA", "is_primary": True},
                {"user": users[3], "street": "321 Elm St", "city": "Miami", "state": "FL",
                    "zip_code": "33101", "country": "USA", "is_primary": True},
                {"user": users[4], "street": "654 Maple Dr", "city": "Seattle",
                    "state": "WA", "zip_code": "98101", "country": "USA", "is_primary": True},
            ]

            for addr_data in addresses_data:
                address = Address(
                    user_id=addr_data["user"].id,
                    street=addr_data["street"],
                    city=addr_data["city"],
                    state=addr_data["state"],
                    zip_code=addr_data["zip_code"],
                    country=addr_data["country"],
                    is_primary=addr_data["is_primary"]
                )
                session.add(address)
            session.commit()

        # Добавляем продукты, если их нет
        existing_products = session.execute(select(Product)).scalars().all()
        if not existing_products:
            products_data = [
                {"name": "Laptop", "description": "High-performance laptop",
                    "price": 999.99},
                {"name": "Smartphone",
                    "description": "Latest smartphone model", "price": 699.99},
                {"name": "Headphones",
                    "description": "Wireless headphones", "price": 199.99},
                {"name": "Tablet", "description": "10-inch tablet", "price": 449.99},
                {"name": "Smartwatch",
                    "description": "Fitness smartwatch", "price": 299.99}
            ]

            products = []
            for product_data in products_data:
                product = Product(
                    name=product_data["name"],
                    description=product_data["description"],
                    price=product_data["price"]
                )
                products.append(product)
                session.add(product)
            session.commit()
        else:
            products = existing_products

        # Добавляем заказы, если их нет
        existing_orders = session.execute(select(Order)).scalars().all()
        if not existing_orders:
            # Получаем адреса для заказов
            addresses = session.execute(select(Address)).scalars().all()

            orders_data = [
                {"user": users[0], "address": addresses[0]},
                {"user": users[1], "address": addresses[1]},
                {"user": users[2], "address": addresses[2]},
                {"user": users[3], "address": addresses[3]},
                {"user": users[4], "address": addresses[4]}
            ]

            orders = []
            for order_data in orders_data:
                order = Order(
                    user_id=order_data["user"].id,
                    delivery_address_id=order_data["address"].id
                )
                orders.append(order)
                session.add(order)
            session.commit()

            # Добавляем элементы заказа
            order_items_data = [
                {"order": orders[0], "product": products[0], "quantity": 1},
                {"order": orders[0], "product": products[2], "quantity": 2},
                {"order": orders[1], "product": products[1], "quantity": 1},
                {"order": orders[1], "product": products[4], "quantity": 1},
                {"order": orders[2], "product": products[3], "quantity": 1},
                {"order": orders[3], "product": products[0], "quantity": 1},
                {"order": orders[3], "product": products[1], "quantity": 1},
                {"order": orders[3], "product": products[2], "quantity": 3},
                {"order": orders[4], "product": products[4], "quantity": 2},
                {"order": orders[4], "product": products[2], "quantity": 1}
            ]

            for item_data in order_items_data:
                order_item = OrderItem(
                    order_id=item_data["order"].id,
                    product_id=item_data["product"].id,
                    quantity=item_data["quantity"]
                )
                session.add(order_item)
            session.commit()

        print("Data update completed")


def check_data():
    """Проверяет количество данных в базе"""
    with Session() as session:
        users = session.execute(select(User)).scalars().all()
        addresses = session.execute(select(Address)).scalars().all()
        products = session.execute(select(Product)).scalars().all()
        orders = session.execute(select(Order)).scalars().all()
        order_items = session.execute(select(OrderItem)).scalars().all()

        print(f"Users: {len(users)}")
        print(f"Addresses: {len(addresses)}")
        print(f"Products: {len(products)}")
        print(f"Orders: {len(orders)}")
        print(f"Order items: {len(order_items)}")


def demo_relationships():
    """Демонстрирует связи между данными"""
    with Session() as session:
        # Полная информация о пользователях с их заказами
        users_stmt = (
            select(User)
            .options(
                selectinload(User.addresses),
                selectinload(User.orders).selectinload(
                    Order.order_items).selectinload(OrderItem.product)
            )
        )
        users = session.execute(users_stmt).scalars().all()

        for user in users:
            print(f"User: {user.username} - {user.description}")
            print(f"Orders: {len(user.orders)}")
            for order in user.orders:
                print(f"  Order #{order.id}:")
                for item in order.order_items:
                    print(
                        f"    - {item.product.name}: {item.quantity} x ${item.product.price}")


if __name__ == "__main__":
    add_or_update_data()  # Добавляет или обновляет данные
    check_data()          # Проверяем данные
    demo_relationships()  # Демонстрируем связи
