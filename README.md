# AskPupkin — Web HW2

Django-проект для домашнего задания: страницы вопросов, формы, именованные маршруты, шаблоны с `extends`/`include` и общая пагинация.

## Локальный запуск

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Откройте: http://127.0.0.1:8000/

## Запуск через Docker Compose

```bash
docker compose up --build
```

Откройте: http://127.0.0.1:8000/

## Проверка

```bash
python manage.py test
```

## Основные URL

- `/` — новые вопросы
- `/hot/` — популярные вопросы
- `/tag/<tag>/` — вопросы по тегу
- `/question/<id>/` — страница вопроса
- `/login/` — вход
- `/signup/` — регистрация
- `/profile/` — профиль
- `/ask/` — новый вопрос
