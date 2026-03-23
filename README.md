# Bill Splitter Bot

Telegram-бот для розподілу спільних витрат у групах (поїздки / події).

- **Документація продукту:** [docs/PRODUCT.md](docs/PRODUCT.md)  
- **Історія змін (обов’язково оновлювати при змінах):** [docs/CHANGELOG.md](docs/CHANGELOG.md)

Локально: скопіюй `.env.example` → `.env`, задай `BOT_TOKEN`, потім `pip install -r requirements.txt` і `python main.py`.

Опційно в `.env`: **`SUPPORT_MONO_URL`** (посилання Mono) — кнопка в `/help` і посилання після завершення події. У **Render** додай змінну в **Environment** (не коміть значення в git).
