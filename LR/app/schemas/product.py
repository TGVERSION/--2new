from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ProductCreate(BaseModel):
    """Схема для создания продукта"""

    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int = 0


class ProductUpdate(BaseModel):
    """Схема для обновления продукта"""

    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[float] = None
    stock_quantity: Optional[int] = None


class ProductResponse(BaseModel):
    """Схема для ответа с данными продукта"""

    id: str
    name: str
    description: Optional[str] = None
    price: float
    stock_quantity: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
