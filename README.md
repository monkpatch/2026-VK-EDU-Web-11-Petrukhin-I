# AskPupkin — Web HW3

Django-проект для ДЗ3: ORM-модели (вопросы/ответы/теги/профиль/лайки), менеджеры выборок, пагинация, наполнение БД через `fill_db`, PostgreSQL и docker-compose с отдельным сервисом БД.

## 1) Локальный запуск (PostgreSQL)

1. Создайте и заполните `.env.local` (можно скопировать из `.env.example`).
2. Поднимите PostgreSQL локально.
3. Запустите:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
set -a; source .env.local; set +a
python manage.py migrate
python manage.py fill_db 100
python manage.py runserver
```

Откройте: http://127.0.0.1:8000/

## 2) Запуск через Docker Compose

```bash
docker compose --env-file .env.docker up --build
```

Сервисы:
- `web` — Django
- `db` — PostgreSQL (с persistent volume `postgres_data`)

## 3) Админка

```bash
python manage.py createsuperuser
```

Админка: http://127.0.0.1:8000/admin/

## 4) Команда наполнения БД

```bash
python manage.py fill_db [ratio]
```

Добавляет:
- users: `ratio`
- questions: `ratio * 10`
- answers: `ratio * 100`
- tags: `ratio`
- likes: `ratio * 200` для вопросов и `ratio * 200` для ответов

## 5) Отладка и проверки

```bash
python manage.py test
python manage.py check
```

`django-debug-toolbar` подключается только при `DJANGO_DEBUG=True`.

## 6) Примечание для быстрых локальных проверок

Можно временно включить SQLite:

```bash
USE_SQLITE=1 python manage.py migrate
```

Для сдачи ДЗ используется PostgreSQL/MySQL (в этом проекте — PostgreSQL).
