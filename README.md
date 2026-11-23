# FullStack Web Development with Python

Домашні роботи Viktoriia Kratser в одному репозиторії. Кожна папка — незалежна робота зі своїми залежностями та інструкцією запуску.

| Робота | Папка | Зміст | Локальна адреса |
|---|---|---|---|
| ДЗ1 | [hw01](hw01/) | Копія вже зданої роботи: фабрики, бібліотека | CLI |
| ДЗ2 | [hw02](hw02/) | FastAPI + PostgreSQL у Docker, Python 3.10 | http://localhost:8002 |
| ДЗ3 | [hw03](hw03/) | HTTP-сервер, форма, JSON, Jinja2, volume | http://localhost:3000 |
| ДЗ4 | [hw04](hw04/) | Асинхронне сортування файлів за розширеннями | CLI |
| ДЗ6 | [hw06](hw06/) | SQLAlchemy, Alembic, Faker, 12 вибірок, CRUD CLI | CLI |
| ДЗ8 | [hw08](hw08/) | REST API контактів, пошук, дні народження | http://localhost:8008/docs |
| ДЗ10 | [hw10](hw10/) | JWT, верифікація пошти, власні контакти, CORS, аватари | http://localhost:8010/docs |
| ДЗ12 | [hw12](hw12/) | Фінальне API: Redis, reset password, ролі, тести, Sphinx | http://localhost:8012/docs |

## Запуск

Відкрийте термінал у папці потрібного ДЗ. Для Docker-робіт потрібен запущений Docker Desktop у режимі Linux containers. Якщо є `.env.example`, скопіюйте його в `.env` перед запуском:

```powershell
Copy-Item .env.example .env
docker compose up --build -d
docker compose logs app
```

Для ДЗ6 послідовність із міграцією та наповненням наведена в його README. `docker compose` — сучасний еквівалент `docker-compose` з умов завдань. Різні імена Compose-проєктів, порти й volumes дозволяють запускати роботи незалежно. Зупинка: `docker compose down` у відповідній папці; дані БД зберігаються у volume.

Приклади `.env.example` призначені для локального навчального запуску. Реальні `.env`, ключі Cloudinary, JWT-секрети, дані БД і користувацькі повідомлення не включаються в Git або ZIP. Для ДЗ10/12 перед публічним розгортанням замініть JWT-секрет та паролі. Для локальної пошти включено Mailpit; реальний SMTP задається через `.env`.

## Здача

За обраною структурою посилання на роботу має вигляд `https://github.com/vikkrat/woolf-python-web/tree/main/hw02`. В умовах LMS зазначені окремі репозиторії `goit-pythonweb-hw-XX`: цей репозиторій навмисно зберігає роботи в папках за побажанням авторки. Якщо ментор вимагає саме окремі репозиторії, папки можна опублікувати окремо без змін коду.

Створення незалежних архівів із кореня репозиторію:

```powershell
python tools/package.py --name "Viktoriia_Kratser"
```

Архіви з'являться в `dist/` з назвами `ДЗ2_Viktoriia_Kratser.zip`, тощо. Скрипт виключає секрети, кеші, локальні БД і згенеровані файли. Завантаження в LMS виконується вручну.

## Джерела

- ДЗ1: https://github.com/vikkrat/goit-pythonweb-hw-01, commit `62d75a2798faed4f6dd13c5f3e7e785d5ec805ad`. Початкові `task_1.py` і `task_2.py` збережені без змін.
- ДЗ2: https://github.com/GoIT-Python-Web/FullStack-Web-Development-hw2, commit `af8e0de01d542c7cdddf623408e8436adae3dca5`. Додано Docker, Compose та налаштування БД.
- ДЗ3: https://github.com/GoIT-Python-Web/FullStack-Web-Development-hw3, commit `1775a267eec837e9e39f2f40238be55fc1b3bbc5`. Збережено вихідні HTML/CSS/logo та додано сервер і шаблон читання.

Фінальна робота реалізує обов'язкові вимоги. Опціональні refresh tokens та хмарне розгортання не включені.
