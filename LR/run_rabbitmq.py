"""Скрипт для запуска обработчиков RabbitMQ"""
import asyncio
import sys
from pathlib import Path

# Добавляем текущую директорию в путь
sys.path.insert(0, str(Path(__file__).parent))

from app.rabbitmq_handlers import app

if __name__ == "__main__":
    async def main():
        await app.run()
    
    asyncio.run(main())

