from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional
from datetime import datetime


class UserCreate(BaseModel):
    """Схема для создания пользователя"""
    username: str
    email: EmailStr
    description: Optional[str] = None


class UserUpdate(BaseModel):
    """Схема для обновления пользователя"""
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    description: Optional[str] = None


class UserResponse(BaseModel):
    """Схема для ответа с данными пользователя"""
    id: str
    username: str
    email: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

