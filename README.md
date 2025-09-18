[![CI/CD Status](https://github.com/Zenchuk-A/foodgram/actions/workflows/main.yml/badge.svg)](https://github.com/Zenchuk-A/foodgram/actions)
## Foodgram - сервис публикации рецептов в рамках учебного курса Яндекс.Практикум
Финальный вариант развёрнут по адресу: foodgram-zen.sytes.net

Foodgram - это веб-приложение для публикации кулинарных рецептов. Пользователи могут:
- Публиковать свои рецепты
- Добавлять чужие рецепты в избранное
- Подписываться на авторов
- Создавать списки покупок для выбранных рецептов
- Фильтровать рецепты по тегам

## Стек технологий
- Backend: Django, Django REST Framework, Djoser
- Database: PostgreSQL
- Frontend: React (отдельный репозиторий)
- Деплой: Docker, Nginx, Gunicorn

## Развертывание в Docker

1. Склонируйте репозиторий:
```bash
git clone https://github.com/Zenchuk-A/foodgram.git
```
```
cd foodgram
```

2. В основной директории проекта создайте файл .env с переменными окружения:
```
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432
SECRET_KEY=yoursecretkey
ALLOWED_HOSTS="127.0.0.1, localhost, ..."
DEBUG=True  # Для отладки
USE_SQLITE=True  # При отладке используется SQLite. Для PostgreSQL установить False
```

3. Запустите контейнеры:
```
docker compose up -d --build
```

4. Выполните миграции:
```
docker compose exec backend python manage.py migrate
```

5. Соберите статику:
```
docker compose exec backend python manage.py collectstatic --no-input
```

6. Создайте суперпользователя:
```
docker compose exec backend python manage.py createsuperuser
```

## Для загрузки данных по ингредиентам выполните:
```
docker compose exec backend python manage.py import_csv
```

## Примеры запросов/ответов
Регистрация пользователя
Запрос:
```
POST /api/users/
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "username",
  "first_name": "Имя",
  "last_name": "Фамилия",
  "password": "string"
}
```
Ответ:
```
{
  "email": "user@example.com",
  "id": 0,
  "username": "username",
  "first_name": "Имя",
  "last_name": "Фамилия"
}
```
Получение списка рецептов
Запрос:
```
GET /api/recipes/
Ответ:
{
  "count": 123,
  "next": "http://foodgram.example.org/api/recipes/?page=4",
  "previous": "http://foodgram.example.org/api/recipes/?page=2",
  "results": [
    {
      "id": 0,
      "tags": [
        {
          "id": 0,
          "name": "Завтрак",
          "slug": "breakfast"
        }
      ],
      "author": {
        "email": "user@example.com",
        "id": 0,
        "username": "string",
        "first_name": "Вася",
        "last_name": "Пупкин",
        "is_subscribed": false
      },
      "ingredients": [
        {
          "id": 0,
          "name": "Картофель отварной",
          "measurement_unit": "г",
          "amount": 1
        }
      ],
      "is_favorited": true,
      "is_in_shopping_cart": true,
      "name": "string",
      "image": "http://foodgram.example.org/media/recipes/images/image.jpeg",
      "text": "string",
      "cooking_time": 1
    }
  ]
}
```
### Автор:
 - Андрей Зенчук
