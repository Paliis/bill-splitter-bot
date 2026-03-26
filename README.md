# Bill Splitter Bot

Telegram-бот для розподілу спільних витрат у групах (поїздки / події).

- **Документація продукту:** [docs/PRODUCT.md](docs/PRODUCT.md)  
- **Архітектура (PWA → магазини, API-first):** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)  
- **Роудмап, етапи:** [docs/ROADMAP.md](docs/ROADMAP.md)  
- **Юридичні чернетки (Privacy / Terms):** [docs/legal/README.md](docs/legal/README.md)  
- **OpenAPI v1 (скелет):** [docs/openapi/README.md](docs/openapi/README.md)  
- **Історія змін (обов’язково оновлювати при змінах):** [docs/CHANGELOG.md](docs/CHANGELOG.md)

Локально: скопіюй `.env.example` → `.env`, задай `BOT_TOKEN`, потім `pip install -r requirements.txt` і `python main.py`.

**Render / прод:** обов’язково задай **`DATABASE_URL`** на **PostgreSQL** (наприклад [Neon](https://neon.tech)) з рядком `postgresql+asyncpg://...`. Якщо залишити SQLite за замовчуванням, файл `bot.db` живе на тимчасовому диску воркера — **після кожного деплою список учасників і витрати зникають**.

Інтерфейс **uk/en** за мовою Telegram (`uk`/`ru` → українська). Опційно в `.env`: **`SUPPORT_MONO_URL`**, **`SUPPORT_BUYMEACOFFEE_URL`** (для en), **`SUPPORT_FEEDBACK_URL`**. У **Render** — ті самі ключі в **Environment**.
