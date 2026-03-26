# Покрокова інструкція: від нуля до робочого бота й API на Render

Цей документ описує **усе, що робите ви** (акаунти, секрети, кліки в панелях). Код у репозиторії вже містить бота, FastAPI і `render.yaml`. Дублі коротко: [DEPLOY_RENDER.md](./DEPLOY_RENDER.md), чеклист: [ROADMAP.md § Чеклист власника](./ROADMAP.md#чеклист-власника).

---

## Крок 0. Що має бути перед стартом

| Що | Навіщо |
|----|--------|
| **Обліковий запис GitHub** | Репозиторій з кодом уже існує; вам потрібен доступ **push** у `main` (або ваша форк/копія). |
| **Обліковий запис [Render](https://render.com)** | Хостинг для worker (бот) і web (API). Є безкоштовний рівень з обмеженнями; для «завжди вмикено» часто потрібен платний план. |
| **PostgreSQL у хмарі** | Обов’язково для **прод**: спільна БД для бота й API. Варіанти: **Neon**, **Supabase**, **Render PostgreSQL**. SQLite на Render **не** підходить — дані зникнуть після деплою. |
| **Телеграм** | Бот створюється через [@BotFather](https://t.me/BotFather); отримаєте **`BOT_TOKEN`**. |

Час: перший раз **30–90 хв** залежно від знайомства з панелями.

---

## Крок 1. Отримати токен бота (BotFather)

1. У Telegram відкрийте **@BotFather**.
2. Команда `/newbot` (якщо бота ще немає) або `/mybots` → оберіть бота → **API Token**.
3. Скопіюйте рядок виду `123456789:AAH…` — це **`BOT_TOKEN`**. **Ніколи** не публікуйте його в чатах і не комітьте в git (лише в `.env` локально та в **Environment** на Render).
4. У BotFather для групового бота корисно: **Group Privacy** зняти або навчити людей `/here` (див. [PRODUCT.md](./PRODUCT.md)).

---

## Крок 2. Створити базу PostgreSQL і рядок `DATABASE_URL`

### Варіант A — Neon (часто найпростіше)

1. Зайдіть на [https://neon.tech](https://neon.tech), створіть проєкт і базу.
2. У консолі Neon скопіюйте **connection string** (зазвичай починається з `postgresql://...`).
3. **Перетворіть на формат для цього проєкту:**
   - Замініть на початку **`postgresql://`** на **`postgresql+asyncpg://`**  
     (саме **`+asyncpg`**, інакше бот не підключиться через SQLAlchemy async).
4. Якщо в кінці URI є **`?sslmode=require`** — **залиште як є**: у коді `database.py` це обробляється для asyncpg.
5. Збережіть повний рядок у безпечне місце — це **`DATABASE_URL`** для **обох** сервісів на Render.

**Приклад перетворення:**

```text
Було:  postgresql://user:pass@host.neon.tech/neondb?sslmode=require
Треба: postgresql+asyncpg://user:pass@host.neon.tech/neondb?sslmode=require
```

### Варіант B — PostgreSQL на самому Render

1. У Render: **New +** → **PostgreSQL**. Створіть інстанс.
2. У картці БД знайдіть **Internal Database URL** або **External**.
3. Так само замініть `postgresql://` на **`postgresql+asyncpg://`** для нашого коду.
4. Переконайтесь, що **обидва** сервіси (worker і web) можуть дістатися до хоста БД (у Render часто використовують internal URL для сервісів у тому ж акаунті).

---

## Крок 3. Репозиторій і локальна копія (опційно, але корисно)

1. Якщо клонуєте собі: `git clone …` і заходьте в папку проєкту.
2. Скопіюйте `.env.example` → **`.env`** у корені.
3. Заповніть **локально** (для тестів):
   - `BOT_TOKEN=…`
   - `DATABASE_URL=…` (можна тимчасово SQLite: `sqlite+aiosqlite:///./bot.db` **тільки для локалки**)
4. Не комітьте `.env` — він у `.gitignore`.

Перевірка без деплою:

```powershell
pip install -r requirements.txt
python scripts/verify_local.py
python main.py
```

Окремо API:

```powershell
$env:PYTHONPATH="."
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

Відкрийте `http://127.0.0.1:8000/health` — має бути `{"status":"ok"}`.

---

## Крок 4. Підключити GitHub до Render

1. Увійдіть на [dashboard.render.com](https://dashboard.render.com).
2. **Account Settings** (або при створенні сервісу) → підключіть **GitHub**.
3. Надайте Render доступ до **репозиторію** `bill-splitter-bot` (або вашого форку).

---

## Крок 5. Створити сервіси: Blueprint або вручну

### Варіант A — Blueprint (рекомендовано, якщо є `render.yaml` у корені)

1. У Render: **New +** → **Blueprint**.
2. Оберіть репозиторій і гілку **`main`**.
3. Render прочитає [render.yaml](../render.yaml) і запропонує **два** сервіси:
   - `bill-splitter-bot` (**Worker**)
   - `bill-splitter-api` (**Web Service**)
4. Застосуйте. Поки **не** задані секрети, деплой може **падати** — це нормально до кроку 6.

### Варіант B — Вручну (якщо Blueprint не підходить)

**Worker (бот):**

1. **New +** → **Background Worker**.
2. Підключіть repo, гілка `main`, **Root** корінь репо.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:** `python main.py`
5. Назва на кшталт `bill-splitter-bot`.

**Web (API):**

1. **New +** → **Web Service**.
2. Той самий repo і гілка.
3. **Build command:** `pip install -r requirements.txt`
4. **Start command:**  
   `PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Назва на кшталт `bill-splitter-api`. **Instance type** оберіть мінімальний план, на якому дозволено Web.

---

## Крок 6. Задати змінні середовища (Environment)

Відкрийте **кожен** сервіс окремо → меню **Environment**.

### Таблиця: що куди

| Змінна | Worker (бот) | Web (API) | Приклад / примітки |
|--------|--------------|-----------|--------------------|
| **`BOT_TOKEN`** | **Так** (обов’язково) | **Ні** (не додавати) | З BotFather |
| **`DATABASE_URL`** | **Так** | **Так** | **Той самий** рядок `postgresql+asyncpg://…` |
| **`API_SECRET`** | Ні | **Так** (сильно рекомендовано в проді) | Випадковий рядок 32+ символи; згенеруйте в менеджері паролів |
| `SUPPORT_MONO_URL` | Опційно | Ні | Посилання Mono для донатів |
| `SUPPORT_BUYMEACOFFEE_URL` | Опційно | Ні | Для en |
| `SUPPORT_FEEDBACK_URL` | Опційно | Ні | Telegram для фідбеку |

Після кожної зміни натисніть **Save Deploy** (або еквівалент), щоб сервіс перебілдився/перезапустився.

**Важливо:** у `render.yaml` для секретів стоїть `sync: false` — значення **не** підтягуються з файлу, їх **треба ввести в UI вручну** один раз.

---

## Крок 7. Дочекатися деплою і переглянути логи

1. Відкрийте сервіс → вкладка **Logs**.
2. **Worker:** має бути старт aiogram polling без `TelegramConflictError`. Якщо бачите conflict — запущено **другий** процес з тим самим токеном (зупиніть дубль).
3. **Web:** має бути рядок на кшталт `Uvicorn running on http://0.0.0.0:PORT`. Якщо traceback про БД — перевірте `DATABASE_URL` і доступність Postgres.

---

## Крок 8. Перевірити бота в Telegram

1. Додайте бота в **групу**, зробіть **адміном** (бажано з правом читати повідомлення).
2. Надішліть `/start` або `/menu`.
3. Створіть тестову поїздку, додайте витрату (див. [PRODUCT.md](./PRODUCT.md)) — у БД з’являться записи (тепер у вже підключеному Postgres).

---

## Крок 9. Перевірити HTTP API

1. У сервісі **Web** скопіюйте **URL** (наприклад `https://bill-splitter-api-xxxx.onrender.com`).
2. **Health (без секрету):**  
   У браузері: `https://…/health` → `{"status":"ok"}`.
3. **Trip (якщо задано `API_SECRET`):**  
   Потрібен заголовок **`X-Api-Secret`** з тим же значенням, що й у Render.

**PowerShell (замініть URL, SECRET і id):**

```powershell
$base = "https://ВАШ-API.onrender.com"
Invoke-RestMethod -Uri "$base/health" -Method Get

$h = @{ "X-Api-Secret" = "ВАШ_API_SECRET" }
Invoke-RestMethod -Uri "$base/v1/trips/1" -Headers $h -Method Get
```

- Якщо поїздки з `id=1` немає — отримаєте **404** — це нормально; головне не **401** (якщо секрет правильний) і не **502**.

Якщо **`API_SECRET` не задано** на Render, ендпоінти `/v1/*` відкриті (у логах буде попередження) — для **продакшену** краще завжди задати секрет.

---

## Крок 10. GitHub Actions (CI)

1. У репозиторії на GitHub: вкладка **Actions**.
2. Після кожного push у **`main`** має виконуватись workflow **CI** (компіляція + імпорт `backend.main`).
3. Якщо workflow вимкнено в налаштуваннях організації — увімкніть для репо.

Це **не** деплой на Render; деплой на Render зазвичай тригериться **push** у підключену гілку, якщо увімкнено **Auto-Deploy**.

---

## Крок 11. Що робити після зміни коду

1. Локально: `python scripts/verify_local.py`.
2. `git add` / `git commit` / **`git push`** у `main`.
3. Render (якщо auto-deploy): дочекайтесь **двох** успішних деплоїв — worker і web **незалежні**; іноді треба перезапусти один, якщи змінювався тільки він.
4. Перевірте знову `/health` і бота в групі.

---

## Крок 12. Типові проблеми (розширено)

| Симптом | Дії |
|---------|-----|
| **Бот мовчить** | Логи worker; чи є `BOT_TOKEN`; чи бот не видалений; чи немає `TelegramConflictError`. |
| **502 на API** | Логи web; чи валідний `DATABASE_URL`; чи Postgres приймає з’єднання з IP Render. |
| **401 на `/v1/trips/...`** | Заголовок `X-Api-Secret` має **точно** збігатися з `API_SECRET` (без лапок і пробілів). |
| **У бота одні дані, в API інші** | Майже завжди різні `DATABASE_URL` — мають бути **ідентичні** рядки. |
| **Після деплою «чиста» база** | Раніше використовували SQLite на диску воркера — переходьте на Postgres і однаковий URL для обох сервісів. |

---

## Де що лежить у репо

| Файл | Зміст |
|------|--------|
| [render.yaml](../render.yaml) | Опис двох сервісів для Blueprint |
| [main.py](../main.py) | Точка входу бота |
| [backend/main.py](../backend/main.py) | FastAPI |
| [database.py](../database.py) | Підключення до БД |
| [docs/openapi/openapi.yaml](./openapi/openapi.yaml) | Контракт API (повна реалізація — у дорожній карті) |

---

## Після успішного деплою

- Пройдіть короткий чеклист у [ROADMAP.md](./ROADMAP.md#чеклист-власника).
- Наступна розробка за планом: **Фаза 1.3** — решта ендпоінтів і нормальна авторизація для PWA.

Якщо застрягли на конкретному кроці — зніміть **скришот логів** (без токенів) і повідомлення помилки; токени й паролі нікуди не надсилайте.
