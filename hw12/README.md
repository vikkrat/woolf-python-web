# ДЗ12 — Фінальна робота

Самостійне продовження API контактів: JWT, перевірка email, доступ лише до власних контактів, Redis, скидання пароля, ролі `user`/`admin`, Cloudinary, тести та Sphinx.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Swagger: http://localhost:8012/docs. Mailpit: http://localhost:8112. БД і Redis не публікують портів на комп'ютер; міграції застосовуються автоматично. Перелік і формат контактних маршрутів відповідають ДЗ8, але кожен із них вимагає bearer token.

## Перевірка сценаріїв

1. `POST /auth/signup`: `{"username":"alice","email":"alice@example.com","password":"MyPassword123!"}`. Статус 201, повторний email — 409. Пароль зберігається тільки як Argon2-хеш.
2. Відкрити лист у Mailpit та підтвердити email. За потреби `POST /auth/request-verification`.
3. **Authorize** у Swagger: username або email + пароль. `/auth/login` приймає поля форми у тілі запиту. Помилкові дані — 401; непідтверджена пошта — 403.
4. Створити контакт через `POST /contacts`, перевірити пошук `GET /contacts?q=...`, оновлення, видалення і `/contacts/birthdays`. Інший користувач не має доступу до цього контакту.
5. `POST /auth/forgot-password` з email: отримати лист, відкрити форму та встановити новий пароль. Або передати `token` з листа та `password` у JSON до `POST /auth/reset-password`. Токен чинний 30 хвилин, одноразовий. Зміна пароля відкликає попередні access/verification/reset tokens через `token_version`. Відповідь запиту відновлення не розкриває існування адреси.
6. `/me` обмежено 10 запитами на 60 секунд у спільному Redis для всіх worker-процесів.
7. Звичайний користувач отримує 403 на зміну аватара. Щоб підвищити роль **власного тестового підтвердженого облікового запису**, використайте локальну адміністративну команду:

```powershell
docker compose exec app python -m app.admin alice@example.com
```

Після цього потрібно увійти повторно. Для реального upload задайте ключі `CLOUDINARY_*` у `.env`, перезапустіть app і виконайте `PATCH /me/avatar`. Підтримуються JPEG/PNG/WebP до 2 MiB. Реєстрація не приймає роль від клієнта; публічного маршруту підвищення ролі немає.

Redis-кеш зберігає лише безпечні поля користувача й метадані авторизації на 60 секунд. При влучанні кешу `get_current_user` не запитує БД. Після зміни пароля, ролі, аватара або підтвердження email запис інвалідується. При недоступності Redis авторизація завершується 503. Зміни облікових записів поза API/CLI можуть залишатися в кеші до завершення TTL.

## Тести й документація

Python 3.12:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements-dev.txt
.venv/Scripts/python -m pytest
.venv/Scripts/python -m sphinx -W -b html docs docs/_build/html
```

Або всередині Docker:

```powershell
docker compose build --build-arg INSTALL_DEV=true app
docker compose run --rm app python -m pytest
docker compose run --rm app python -m sphinx -W -b html docs docs/_build/html
```

`pytest.ini` вимагає покриття щонайменше 76% (тобто понад 75%). Модульні тести перевіряють репозиторій, токени та адаптери; HTTP-інтеграційні — маршрути, конфлікти, ownership, reset, ролі, CORS, ліміт. Ізольовані тести використовують SQLite, Redis/SMTP/Cloudinary підмінено; окремий `tools/smoke.py` у корені репозиторію перевіряє запущені Docker-сервіси зі справжніми PostgreSQL, Redis і Mailpit. Реальний Cloudinary вимагає ваших ключів і не перевіряється без них.

## Налаштування

Усі налаштування читаються з `.env`; приклад — `.env.example`. Замініть демонстраційний `JWT_SECRET` випадковим значенням щонайменше 32 символи. Для зовнішнього SMTP задайте `SMTP_*`, `MAIL_FROM` та `PUBLIC_URL`; `CORS_ORIGINS` — JSON-масив адрес фронтенду. Документація після локальної збірки: `docs/_build/html/index.html`.

Опціональні refresh-token flow та хмарний деплой не реалізовані. Усі обов'язкові частини фінального завдання включено.
