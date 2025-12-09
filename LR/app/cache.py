import asyncio
import json
import os
from typing import Optional

import redis.asyncio as redis
from pydantic import BaseModel


class CacheService:
    """Сервис для работы с Redis кэшем"""

    def __init__(self, redis_client: redis.Redis):
        """
        Инициализация сервиса кэша

        Args:
            redis_client: Клиент Redis
        """
        self.redis_client = redis_client

    async def get(self, key: str) -> Optional[str]:
        """
        Получить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            Значение из кэша или None
        """
        try:
            value = await asyncio.wait_for(self.redis_client.get(key), timeout=1.0)
            return value.decode("utf-8") if value else None
        except (asyncio.TimeoutError, redis.RedisError, ConnectionError, OSError):
            return None

    async def set(self, key: str, value: str, ttl: int) -> bool:
        """
        Установить значение в кэш с TTL

        Args:
            key: Ключ кэша
            value: Значение для кэширования
            ttl: Время жизни в секундах

        Returns:
            True если успешно, False в противном случае
        """
        try:
            await asyncio.wait_for(
                self.redis_client.setex(key, ttl, value), timeout=1.0
            )
            return True
        except (asyncio.TimeoutError, redis.RedisError, ConnectionError, OSError):
            return False

    async def delete(self, key: str) -> bool:
        """
        Удалить значение из кэша

        Args:
            key: Ключ кэша

        Returns:
            True если успешно, False в противном случае
        """
        try:
            await asyncio.wait_for(self.redis_client.delete(key), timeout=1.0)
            return True
        except (asyncio.TimeoutError, redis.RedisError, ConnectionError, OSError):
            return False

    async def get_model(
        self, key: str, model_class: type[BaseModel]
    ) -> Optional[BaseModel]:
        """
        Получить модель из кэша

        Args:
            key: Ключ кэша
            model_class: Класс Pydantic модели

        Returns:
            Экземпляр модели или None
        """
        value = await self.get(key)
        if value:
            try:
                data = json.loads(value)
                return model_class(**data)
            except (json.JSONDecodeError, ValueError, TypeError, KeyError):
                return None
        return None

    async def set_model(self, key: str, model: BaseModel, ttl: int) -> bool:
        """
        Сохранить модель в кэш

        Args:
            key: Ключ кэша
            model: Экземпляр Pydantic модели
            ttl: Время жизни в секундах

        Returns:
            True если успешно, False в противном случае
        """
        try:
            value = json.dumps(model.model_dump(), default=str)
            return await self.set(key, value, ttl)
        except (TypeError, ValueError, AttributeError):
            return False

    async def ping(self) -> bool:
        """
        Проверить подключение к Redis

        Returns:
            True если подключение установлено
        """
        try:
            await self.redis_client.ping()
            return True
        except (redis.RedisError, ConnectionError, OSError):
            return False


async def create_redis_client() -> redis.Redis:
    """
    Создать клиент Redis

    Returns:
        Клиент Redis
    """
    redis_host = os.getenv("REDIS_HOST", "localhost")
    redis_port = int(os.getenv("REDIS_PORT", "6379"))
    redis_db = int(os.getenv("REDIS_DB", "0"))

    return redis.Redis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
        decode_responses=False,  # Получаем bytes для decode_responses=True в методах
        socket_connect_timeout=2,  # Таймаут подключения 2 секунды
        socket_timeout=2,  # Таймаут операций 2 секунды
        retry_on_timeout=True,
        health_check_interval=30,  # Проверка здоровья каждые 30 секунд
    )


# Константы для TTL
USER_CACHE_TTL = 3600  # 1 час для пользователей
PRODUCT_CACHE_TTL = 600  # 10 минут для продукции

# Префиксы для ключей кэша
USER_CACHE_PREFIX = "user:"
PRODUCT_CACHE_PREFIX = "product:"
