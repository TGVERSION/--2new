#!/bin/bash
# Применение миграций
alembic upgrade head

# Запуск приложения
exec "$@"

