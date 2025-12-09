# Инструкция по запуску приложения

## Установка зависимостей

1. Убедитесь, что у вас установлен Python 3.10 или выше
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Запуск приложения

### Важно: Запуск должен выполняться из директории LR

1. Перейдите в директорию LR:
```bash
cd LR
```

2. Запустите RabbitMQ через Docker Compose:
```bash
docker-compose up -d rabbitmq
```

3. Запустите обработчики RabbitMQ (в отдельном терминале):
```bash
python run_rabbitmq.py
```

4. Запустите основное приложение Litestar (в отдельном терминале):
```bash
python run_app.py
```

Или используйте команды напрямую:
```bash
# Обработчики RabbitMQ
python -m app.rabbitmq_handlers

# Основное приложение
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

5. Запустите продюсер для отправки тестовых данных:
```bash
python producer.py
```


## Проверка работы

После запуска приложение будет доступно по адресу:
- http://localhost:8000
- RabbitMQ UI: http://localhost:15672 (логин/пароль: guest/guest)

### Доступные API endpoints:

#### Пользователи (`/users`):
- **GET** `/users` - Получить список пользователей
  - Параметры запроса: `?page=1&count=10&username=...&email=...&description=...`
  
- **GET** `/users/{user_id}` - Получить пользователя по ID
  
- **POST** `/users` - Создать нового пользователя
  - Тело запроса: `{"username": "test", "email": "test@example.com", "description": "..."}`
  
- **PUT** `/users/{user_id}` - Обновить пользователя
  
- **DELETE** `/users/{user_id}` - Удалить пользователя

#### Заказы (`/orders`):
- **GET** `/orders` - Получить список заказов
  - Параметры запроса: `?page=1&count=10`
  
- **GET** `/orders/{order_id}` - Получить заказ по ID

#### Продукция (`/products`):
- **GET** `/products` - Получить список продукции
  - Параметры запроса: `?page=1&count=10`
  
- **GET** `/products/{product_id}` - Получить продукцию по ID

### RabbitMQ очереди:

- **order** - очередь для обработки заказов
  - Операции: `create`, `update`
  
- **product** - очередь для обработки продукции
  - Операции: `create`, `update`, `mark_out_of_stock`

## Запуск тестов

### Подготовка

Перед запуском тестов убедитесь, что Redis запущен:

```bash
docker-compose up -d redis
```

### Все тесты
```bash
python -m pytest
```

### Только unit-тесты
```bash
python -m pytest tests/test_models/ tests/test_repositories/ tests/test_services/
```

### Только API тесты
```bash
python -m pytest tests/test_routes/
```

### Тесты кэширования
```bash
# Все тесты кэширования (требуется Redis)
python -m pytest tests/test_cache.py tests/test_cache_integration.py -v

# Только unit-тесты кэширования (без Redis)
python -m pytest tests/test_cache.py::TestCacheService -v
```

### С покрытием кода
```bash
python -m pytest --cov=app --cov-report=html
```

### Параллельный запуск
```bash
python -m pip install --force-reinstall pytest-xdist
python -m pytest -n auto
```