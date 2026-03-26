# Bill Splitter API (FastAPI)

Окремий процес від Telegram-бота. На **Render** — тип сервісу **Web** (див. кореневий `render.yaml`).

## Локально

З кореня репозиторія (бо імпортуються `database`, `models`):

```bash
pip install -r requirements.txt
# .env з DATABASE_URL (як у бота)
set PYTHONPATH=.
# Windows PowerShell: $env:PYTHONPATH="."
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

- `GET http://127.0.0.1:8000/health` — без ключа.
- `GET http://127.0.0.1:8000/v1/trips/1` — якщо в `.env` є `API_SECRET`, додайте заголовок `X-Api-Secret: <значення>`.

## Render

У сервісі **bill-splitter-api** задайте той самий **`DATABASE_URL`**, що й у воркера бота, і випадковий **`API_SECRET`**. **`BOT_TOKEN`** для API не потрібен.

Контракт: [docs/openapi/openapi.yaml](../docs/openapi/openapi.yaml).
