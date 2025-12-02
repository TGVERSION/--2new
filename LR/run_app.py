"""Скрипт для запуска основного приложения Litestar"""
import uvicorn
import sys

# По умолчанию порт 8000, но можно указать другой через аргумент
port = 8000
if len(sys.argv) > 1:
    try:
        port = int(sys.argv[1])
    except ValueError:
        print(f"Использование: python run_app.py [порт]")
        print(f"Пример: python run_app.py 8001")
        sys.exit(1)

if __name__ == "__main__":
    print(f"Запуск приложения на http://localhost:{port}")
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=True)

