# Деплой на Render (схема A: бот + API)

**Покроково дуже детально:** [STEP_BY_STEP.md](./STEP_BY_STEP.md).

Один репозиторій, **два сервіси**, **одна PostgreSQL** (`DATABASE_URL`). Чеклист власника — [ROADMAP.md → «Чеклист власника»](./ROADMAP.md#чеклист-власника).

## 1. База даних

Створіть **PostgreSQL** на Render (або [Neon](https://neon.tech) тощо). Скопіюйте URI й перетворіть на формат SQLAlchemy async:

`postgresql://...` → **`postgresql+asyncpg://...`**

Параметри на кшталт `sslmode=require` у рядку Neon бот і API **вже вміють** спростити для asyncpg (див. `database.py`).

## 2. Сервіс «бот» (Worker)

- Тип: **Background Worker** (як у [render.yaml](../render.yaml) — `bill-splitter-bot`).
- **Build:** `pip install -r requirements.txt`
- **Start:** `python main.py`
- **Environment:** `BOT_TOKEN`, `DATABASE_URL` (обов’язково); опційно посилання підтримки.

## 3. Сервіс «API» (Web)

- Тип: **Web Service** — `bill-splitter-api`.
- **Build:** той самий `pip install -r requirements.txt`
- **Start:** `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Environment:**
  - **`DATABASE_URL`** — той самий, що в бота.
  - **`API_SECRET`** — довгий випадковий рядок; той самий можна використовувати для ручних викликів з заголовком `X-Api-Secret`.
- **`BOT_TOKEN` не задавати** — не потрібен.

## 4. Blueprint

Якщо підключено **Blueprint** з репо: після push на `main` Render створює/оновлює сервіси з [render.yaml](../render.yaml). У кожному сервісі з `sync: false` **вручну** введіть секрети (`BOT_TOKEN`, `DATABASE_URL`, `API_SECRET`).

## 5. Швидка перевірка після деплою

1. У вкладці **API** скопіюйте URL (наприклад `https://bill-splitter-api.onrender.com`).
2. Браузер або curl: `GET .../health` → очікуйте `{"status":"ok"}`.
3. `GET .../v1/trips/1` з заголовком `X-Api-Secret: <ваш API_SECRET>` — якщо в БД є поїздка з `id=1`; інакше `404`.

## 6. Типові проблеми

| Симптом | Що перевірити |
|---------|----------------|
| API 502 / crash on start | Логи Web Service: `DATABASE_URL`, чи доступна БД з Render |
| 401 на `/v1/*` | Чи збігається `X-Api-Secret` з `API_SECRET` у env |
| Бот працює, API ні | Чи **Web**, а не Worker; чи `$PORT` у команді старту |
| Дані «не ті» | Чи **той самий** `DATABASE_URL`, що й у воркера |
