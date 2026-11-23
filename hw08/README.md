# ДЗ8 — REST API контактів

Самостійна версія без автентифікації, відповідно до вимог ДЗ8. FastAPI, PostgreSQL, SQLAlchemy, Pydantic, Alembic.

```powershell
Copy-Item .env.example .env
docker compose up --build -d
```

Swagger: http://localhost:8008/docs. Міграції застосовуються автоматично перед запуском API.

| Метод | Маршрут | Дія |
|---|---|---|
| POST | `/contacts` | Створити, статус 201 |
| GET | `/contacts?q=olena&skip=0&limit=100` | Список або пошук за ім'ям, прізвищем, email |
| GET | `/contacts/birthdays` | Дні народження протягом 7 днів |
| GET | `/contacts/{id}` | Один контакт |
| PUT | `/contacts/{id}` | Повне оновлення |
| DELETE | `/contacts/{id}` | Видалення, статус 204 |

```json
{
  "first_name": "Олена",
  "last_name": "Коваль",
  "email": "olena@example.com",
  "phone": "+380501234567",
  "birthday": "2000-01-01",
  "additional_data": "Колега"
}
```

Email унікальний, дати народження в майбутньому відхиляються. Пошук `q` нечутливий до регістру, спеціальні символи SQL LIKE трактуються буквально. Сім днів — сьогодні та наступні шість; перехід року враховано. Народження 29 лютого у невисокосний рік відзначається 28 лютого. Пагінація доступна також для днів народження.

Тести: встановіть `requirements-dev.txt`, потім `python -m pytest -q`. Вони використовують ізольовану SQLite, робочий Compose — PostgreSQL.
