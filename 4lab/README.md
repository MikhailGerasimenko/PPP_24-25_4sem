# API Библиотеки

Это FastAPI приложение для управления библиотекой, которое позволяет работать с авторами и книгами.

## Установка

1. Создайте виртуальное окружение:
```bash
python -m venv venv
source venv/bin/activate  # для Linux/MacOS
# или
venv\Scripts\activate  # для Windows
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Запуск

Для запуска приложения выполните:

```bash
uvicorn app.main:app --reload
```

Приложение будет доступно по адресу http://localhost:8000

## API Документация

После запуска приложения, документация API будет доступна по следующим адресам:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Основные эндпоинты

### Авторы
- GET /authors - получить список всех авторов
- POST /authors - создать нового автора
- GET /authors/{id} - получить информацию об авторе
- PUT /authors/{id} - обновить информацию об авторе
- DELETE /authors/{id} - удалить автора

### Книги
- GET /books - получить список всех книг (можно фильтровать по author_id)
- POST /books - создать новую книгу 