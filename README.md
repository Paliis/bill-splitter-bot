# Bill Splitter Bot

Telegram-бот для розподілу спільних витрат у групах (поїздки / події).

- **Документація продукту:** [docs/PRODUCT.md](docs/PRODUCT.md)  
- **Історія змін (обов’язково оновлювати при змінах):** [docs/CHANGELOG.md](docs/CHANGELOG.md)

Локально: скопіюй `.env.example` → `.env`, задай `BOT_TOKEN`, потім `pip install -r requirements.txt` і `python main.py`.

**Render / прод:** обов’язково задай **`DATABASE_URL`** на **PostgreSQL** (наприклад [Neon](https://neon.tech)) з рядком `postgresql+asyncpg://...`. Якщо залишити SQLite за замовчуванням, файл `bot.db` живе на тимчасовому диску воркера — **після кожного деплою список учасників і витрати зникають**.

Опційно в `.env`: **`SUPPORT_MONO_URL`**, **`SUPPORT_FEEDBACK_URL`** (наприклад `https://t.me/…` для кнопки «Написати розробнику» в `/help`). У **Render** — ті самі ключі в **Environment** (не коміть значення в git).
