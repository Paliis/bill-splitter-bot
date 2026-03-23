# Bill Splitter Bot

Telegram-бот для розподілу спільних витрат у групах (поїздки / події).

- **Документація продукту:** [docs/PRODUCT.md](docs/PRODUCT.md)  
- **Історія змін (обов’язково оновлювати при змінах):** [docs/CHANGELOG.md](docs/CHANGELOG.md)

Локально: скопіюй `.env.example` → `.env`, задай `BOT_TOKEN`, потім `pip install -r requirements.txt` і `python main.py`.

Опційно в `.env`: **`SUPPORT_MONO_URL`** (посилання Mono «банка» / джар) і **`SUPPORT_BUYMEACOFFEE_URL`** — кнопки в `/help` і текстові посилання після завершення події. У **Render** додай ті самі змінні в **Environment** сервісу (не коміть значення в git).
