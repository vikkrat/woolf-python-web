# ДЗ3 — HTTP-сервер повідомлень

Python 3.12. Основа HTML/CSS/logo — офіційний шаблон GoIT.

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install -r requirements.txt
.venv/Scripts/python main.py
```

Або Docker з папкою збереження на комп'ютері:

```powershell
docker compose up --build -d
```

- http://localhost:3000/ — `index.html`.
- http://localhost:3000/message — форма `username` + `message`.
- http://localhost:3000/read — усі повідомлення у шаблоні Jinja2 з HTML-екрануванням.
- `/style.css`, `/logo.png` — статичні файли; невідомі адреси повертають `error.html` зі статусом 404.

Форма записує повідомлення у `storage/data.json` під ключем `str(datetime.now())`. Запис захищено блокуванням потоків і атомарною заміною файлу; старі повідомлення зберігаються. Порожні поля відхиляються. Docker монтує `./storage:/app/storage`, тож повідомлення переживають видалення контейнера. Файл JSON створюється при першому повідомленні та не комітиться. Підтримується один процес сервера на сховище.

Тест: `python -m pip install pytest`, потім `python -m pytest -q`.
