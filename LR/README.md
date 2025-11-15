# Инструкция по запуску приложения

## Установка зависимостей

1. Убедитесь, что у вас установлен Python 3.10 или выше
2. Установите зависимости:

```bash
pip install -r requirements.txt
```

## Запуск приложения


```bash
cd --2new/ЛР2
python -m app.main
```


## Проверка работы

После запуска приложение будет доступно по адресу:
- http://localhost:8000/users

### Доступные API endpoints:

Все эндпоинты находятся по пути `/users`:

- **GET** `/users` - Получить список пользователей
  - Параметры запроса: `?page=1&count=10&username=...&email=...&description=...`
  
- **GET** `/users/{user_id}` - Получить пользователя по ID
  - Пример: `GET /users/42038a64-e04f-4ef6-8442-4d00afc969b5`
  
- **POST** `/users` - Создать нового пользователя
  - Тело запроса: `{"username": "test", "email": "test@example.com", "description": "..."}`
  
- **PUT** `/users/{user_id}` - Обновить пользователя
  - Пример: `PUT /users/42038a64-e04f-4ef6-8442-4d00afc969b5`
  - Тело запроса: `{"username": "new_name", "email": "new@example.com", "description": "..."}`
  
- **DELETE** `/users/{user_id}` - Удалить пользователя
  - Пример: `DELETE /users/42038a64-e04f-4ef6-8442-4d00afc969b5`

Запрос к корневому пути `/` вернет 404, так как все роуты находятся под `/users`.