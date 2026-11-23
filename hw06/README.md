# ДЗ6 — Університетська база даних

PostgreSQL 16, SQLAlchemy 2, Alembic, Faker. Моделі: `Group`, `Student`, `Teacher`, `Subject`, `Grade`. Оцінки від 1 до 100, із датою отримання та зовнішніми ключами.

```powershell
Copy-Item .env.example .env
docker compose up -d db
docker compose build app
docker compose run --rm app alembic upgrade head
docker compose run --rm app python seed.py
docker compose run --rm app python my_select.py 1
```

Наповнення: 40 студентів, 3 групи, 4 викладачі, 7 предметів, від 10 до 20 оцінок у кожного студента сумарно за всіма предметами. Faker використовує українську локаль. Повторне наповнення непорожньої БД відхиляється, щоб не дублювати дані.

У `my_select.py` реалізовано `select_1`–`select_10` за порядком умови та додаткові `select_11` і `select_12`. Відвідування курсу визначається наявністю оцінки. Останнє заняття у №12 визначається максимальною датою саме для заданої групи та предмета.

```powershell
docker compose run --rm app python my_select.py 7 --group-id 1 --subject-id 2
docker compose run --rm app python my_select.py 10 --student-id 1 --teacher-id 1
docker compose run --rm app python my_select.py 12 --group-id 1 --subject-id 1
```

Додатковий CRUD CLI підтримує всі п'ять моделей:

```powershell
docker compose run --rm app python main.py -a create -m Teacher -n "Boris Jonson"
docker compose run --rm app python main.py -a list -m Teacher
docker compose run --rm app python main.py -a update -m Teacher --id 5 -n "Andry Bezos"
docker compose run --rm app python main.py -a remove -m Teacher --id 5
docker compose run --rm app python main.py -a create -m Student -n "New Student" --group-id 1
docker compose run --rm app python main.py -a create -m Subject -n "Physics" --teacher-id 1
docker compose run --rm app python main.py -a create -m Grade --student-id 1 --subject-id 1 --value 95 --received-at 2026-01-15
```

При локальному запуску встановіть `requirements.txt` і задайте `DATABASE_URL` до доступного PostgreSQL. За замовчуванням порт БД не опубліковано: наведені команди запускаються всередині мережі Compose.
