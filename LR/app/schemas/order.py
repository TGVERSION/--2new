from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime


class OrderItemCreate(BaseModel):
    """Схема для создания элемента заказа"""
    product_id: str
    quantity: int


class OrderCreate(BaseModel):
    """Схема для создания заказа"""
    user_id: str
    delivery_address_id: str
    items: List[OrderItemCreate]


class OrderUpdate(BaseModel):
    """Схема для обновления заказа"""
    delivery_address_id: Optional[str] = None


class OrderItemResponse(BaseModel):
    """Схема для ответа с данными элемента заказа"""
    id: str
    order_id: str
    product_id: str
    quantity: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderResponse(BaseModel):
    """Схема для ответа с данными заказа"""
    id: str
    user_id: str
    delivery_address_id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

