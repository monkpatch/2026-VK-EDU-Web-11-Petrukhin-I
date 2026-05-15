# AskPupkin — Web HW5

Django-проект AskPupkin для ДЗ1–ДЗ5: шаблоны и маршрутизация, ORM-модели вопросов/ответов/тегов/профилей/лайков, менеджеры выборок, пагинация, формы и авторизация, загрузка аватарок через `MEDIA_ROOT`, AJAX-голосования и отметка правильного ответа. Для основной БД используется PostgreSQL, для быстрых локальных проверок доступен SQLite через `USE_SQLITE=1`.

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
USE_SQLITE=1 python manage.py test
USE_SQLITE=1 python manage.py check
USE_SQLITE=1 python manage.py makemigrations --check --dry-run
```

`django-debug-toolbar` подключается только при `DJANGO_DEBUG=True`.

## 6) Что реализовано к ДЗ4–ДЗ5

- регистрация, логин, POST-logout с CSRF и безопасным `next`;
- создание вопросов/ответов через Django Forms с сохранением ошибок формы;
- профиль пользователя с загрузкой аватарки в media и валидацией типа/размера файла;
- локальные static-ассеты, включая jQuery для AJAX;
- AJAX like/dislike для вопросов и ответов с JSON-ошибками;
- AJAX-отметка правильного ответа только автором вопроса;
- динамические Popular Tags и Best Members в сайдбаре.

## 7) Примечание для быстрых локальных проверок

Можно временно включить SQLite:

```bash
USE_SQLITE=1 python manage.py migrate
```

Для сдачи ДЗ используется PostgreSQL/MySQL (в этом проекте — PostgreSQL).
