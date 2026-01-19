# Запуск проекта через docker compose на локальной машине
1. В корневой директории .env со следующими данными
   ```
    AUTH_COOKIE_REFRESH=refresh_token
    AUTH_COOKIE_SECURE=
    AUTH_COOKIE_HTTP_ONLY=1
    AUTH_COOKIE_PATH=/refresh
    AUTH_COOKIE_SAMESITE=Lax
    ACCESS_TOKEN_LIFETIME=10
    REFRESH_TOKEN_LIFETIME=30
    SIGNING_KEY=django-insecure-m+_z(e!&1gs_prvjhx1m^hmm+(&%c5hey*e$*ow&c5wva0nhzq
    ENCRYPTION_KEY=XXXXXXXXXXXXXXXXXXXXXXXXX

    CELERY_BROKER_URL=redis://redis:6379
    CELERY_RESULT_BACKEND=redis://redis:6379

    SECRET_KEY=XXXXXXXXXXXXXXXXXXXXXXXXXXX

    MARIADB_DATABASE=hr_project
    MARIADB_USER=hr_project
    MARIADB_PASSWORD=XXXXXXXXXXXXXXX
    MARIADB_HOST=mariadb
    MARIADB_PORT=3306
    MARIADB_ROOT_PASSWORD=XXXXXXXXXXXX
    MARIADB_ROOT_HOST=%
   ```
2. В корне проекта выполнить команду:
Для dev
  ```
  docker compose -f docker-compose.dev.yaml up --build
  ```
Для prod
  ```
  docker compose -f docker-compose.prod.yaml up --build -d
  ```
Сбор статики в новом терминале для prod
  ```
  docker compose exec backend python manage.py collectstatic
  ```
3. В новом терминале выполнить команду:
  ```
  docker compose exec backend python manage.py createsuperuser
  ```
4. Зайдите в панель администратора и создайте настройки системы
5. Полезные ссылки

📘 Swagger / OpenAPI документация
http://127.0.0.1:7000/api/v1/docs

🛠 Административная панель Django
http://127.0.0.1:7000/admin