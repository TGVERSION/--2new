from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, String, Boolean, DateTime, Text, Integer, Float
import uuid
from datetime import datetime

# Базовый класс для всех моделей
Base = declarative_base()


class User(Base):
    """Модель пользователя"""
    __tablename__ = 'users'

    # Уникальный идентификатор пользователя
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    # Имя пользователя (уникальное)
    username: Mapped[str] = mapped_column(
        String(50), nullable=False, unique=True)
    # Электронная почта (уникальная)
    email: Mapped[str] = mapped_column(
        String(100), nullable=False, unique=True)
    # Дополнительное поле: описание пользователя
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Дата создания записи
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)
    # Дата последнего обновления
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)

    # Связь с адресами пользователя (один-ко-многим)
    addresses = relationship("Address", back_populates="user")
    # Связь с заказами пользователя (один-ко-многим)
    orders = relationship("Order", back_populates="user")


class Address(Base):
    """Модель адреса"""
    __tablename__ = 'addresses'

    # Уникальный идентификатор адреса
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    # Внешний ключ к пользователю
    user_id: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False)
    # Улица и дом
    street: Mapped[str] = mapped_column(String(200), nullable=False)
    # Город
    city: Mapped[str] = mapped_column(String(50), nullable=False)
    # Штат/область
    state: Mapped[str] = mapped_column(String(50))
    # Почтовый индекс
    zip_code: Mapped[str] = mapped_column(String(20))
    # Страна
    country: Mapped[str] = mapped_column(String(50), nullable=False)
    # Флаг основного адреса
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    # Дата создания записи
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)
    # Дата последнего обновления
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)

    # Связь с пользователем (многие-к-одному)
    user = relationship("User", back_populates="addresses")
    # Связь с заказами, доставляемыми на этот адрес (один-ко-многим)
    orders = relationship("Order", back_populates="delivery_address")


class Product(Base):
    """Модель продукции"""
    __tablename__ = 'products'

    # Уникальный идентификатор продукта
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    # Название продукта
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    # Описание продукта
    description: Mapped[str] = mapped_column(Text, nullable=True)
    # Цена продукта
    price: Mapped[float] = mapped_column(Float, nullable=False)
    # Дата создания записи
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)
    # Дата последнего обновления
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)

    # Связь с элементами заказа (один-ко-многим)
    order_items = relationship("OrderItem", back_populates="product")


class Order(Base):
    """Модель заказа"""
    __tablename__ = 'orders'

    # Уникальный идентификатор заказа
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    # Внешний ключ к пользователю, сделавшему заказ
    user_id: Mapped[str] = mapped_column(
        ForeignKey('users.id'), nullable=False)
    # Внешний ключ к адресу доставки
    delivery_address_id: Mapped[str] = mapped_column(
        ForeignKey('addresses.id'), nullable=False)
    # Дата создания заказа
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)
    # Дата последнего обновления заказа
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now, onupdate=datetime.now)

    # Связь с пользователем (многие-к-одному)
    user = relationship("User", back_populates="orders")
    # Связь с адресом доставки (многие-к-одному)
    delivery_address = relationship("Address", back_populates="orders")
    # Связь с элементами заказа (один-ко-многим)
    order_items = relationship("OrderItem", back_populates="order")


class OrderItem(Base):
    """Модель элемента заказа (связь между заказом и продукцией)"""
    __tablename__ = 'order_items'

    # Уникальный идентификатор элемента заказа
    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
        default=lambda: str(uuid.uuid4())
    )
    # Внешний ключ к заказу
    order_id: Mapped[str] = mapped_column(
        ForeignKey('orders.id'), nullable=False)
    # Внешний ключ к продукту
    product_id: Mapped[str] = mapped_column(
        ForeignKey('products.id'), nullable=False)
    # Количество продукции в заказе
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    # Дата создания записи
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.now)

    # Связь с заказом (многие-к-одному)
    order = relationship("Order", back_populates="order_items")
    # Связь с продуктом (многие-к-одному)
    product = relationship("Product", back_populates="order_items")
