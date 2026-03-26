# HTTP API v1 — контракт

Файл **[openapi.yaml](./openapi.yaml)** — **скелет** REST API для того самого домену, що й Telegram-бот (поїздки, витрати, баланси, settlement). Реалізації (FastAPI тощо) ще немає — це наступні кроки **Фази 1** у [ROADMAP.md](../ROADMAP.md).

## Як читати MVP-мепінг

- **`partyId`** у шляхах — ідентифікатор **простору події** ([ARCHITECTURE.md](../ARCHITECTURE.md) §0.1). У першій імплементації для Telegram **`party_id` = внутрішній `chats.id`** у БД бота (після мапінгу з `telegram_chat_id`).
- Після появи веб-party без Telegram поле може посилатися на окремий рядок `parties`; контракт шляхів за потреби версіонується (`/v2`) або розширюється.

## Валідація специфікації

Локально (за наявності [Redocly CLI](https://redocly.com/docs/cli/) або `swagger-cli`):

```bash
npx @redocly/cli lint docs/openapi/openapi.yaml
```

Або завантажити YAML у [Swagger Editor](https://editor.swagger.io/).

## Наступний покроковий крок (після цього файлу)

1. Підняти **FastAPI** (або інший фреймворк) у `backend/` або корені репо.
2. Реалізувати **health** + **GET /v1/trips/{tripId}** (read-only) поверх існуючої БД.
3. Додати **авторизацію** (JWT + заголовок / сесія для Telegram bridge).
