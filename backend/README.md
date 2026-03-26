# Bill Splitter API (FastAPI)

Окремий процес від Telegram-бота. На **Render** — тип сервісу **Web** (див. кореневий `render.yaml`).

## Локально

Швидка перевірка без сервера (з кореня репо):

```bash
python scripts/verify_local.py
```

Запуск API (імпортуються `database`, `models` з кореня):

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

Покроково: [docs/DEPLOY_RENDER.md](../docs/DEPLOY_RENDER.md). Коротко: у **bill-splitter-api** той самий **`DATABASE_URL`**, що й у бота, плюс **`API_SECRET`**; **`BOT_TOKEN`** не потрібен.

Чеклист власника: [docs/ROADMAP.md#чеклист-власника](../docs/ROADMAP.md#чеклист-власника).

Контракт: [docs/openapi/openapi.yaml](../docs/openapi/openapi.yaml).
