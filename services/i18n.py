from __future__ import annotations

from typing import Literal

Locale = Literal["uk", "en"]

SUPPORTED_CURRENCIES: tuple[str, ...] = ("UAH", "USD", "EUR", "PLN", "GBP")


def locale_from_telegram(lang_code: str | None) -> Locale:
    if not lang_code:
        return "uk"
    base = lang_code.lower().split("-", 1)[0]
    if base in ("uk", "ru"):
        return "uk"
    return "en"


def tr(locale: Locale, key: str, **kwargs: object) -> str:
    s = STRINGS.get(locale, {}).get(key) or STRINGS["uk"].get(key) or key
    if kwargs:
        return s.format(**kwargs)
    return s


def format_currency_amount(locale: Locale, amount_str: str, currency_code: str) -> str:
    """Підпис суми: 10.00 грн / 10.00 UAH / 10.00 USD."""
    cc = (currency_code or "UAH").upper()
    if locale == "uk" and cc == "UAH":
        return f"{amount_str} грн"
    return f"{amount_str} {cc}"


# Ключі — стабільні ідентифікатори; значення — HTML де потрібно.
STRINGS: dict[Locale, dict[str, str]] = {
    "uk": {
        "menu.caption": (
            "👋 Привіт! Я — ваш <b>Bill Splitter</b>.\n"
            "Допоможу компанії розібратися з грошима без зайвих суперечок. "
            "Щоб я бачив усіх, хто має ділити витрати, хай напишуть щось у чат або один раз <code>/here</code>.\n\n"
            "<b>Як почати?</b>\n"
            "1️⃣ Створіть <b>«Нову поїздку / подію»</b>.\n"
            "2️⃣ Додавайте витрати — кнопка <b>«Додати витрату»</b>.\n"
            "3️⃣ Наприкінці — <b>«Завершити»</b>: скажу, хто кому скільки винен.\n\n"
            "Оберіть дію нижче або згадайте мене через @; також <code>/menu</code>.\n\n"
            "<i>Під час майстра витрати: <code>/cancel</code> — вийти й далі писати в чат.</i>"
        ),
        "btn.new_trip": "🆕 Нова поїздка / подія",
        "btn.add_expense": "💸 Додати витрату",
        "btn.status": "📊 Статус",
        "btn.finish": "🏁 Завершити",
        "btn.help": "❓ Допомога",
        "btn.cancel": "❌ Скасувати",
        "btn.stop_wizard": "🛑 Вийти з майстра",
        "btn.back_actions": "🔙 До вибору дій",
        "btn.support_mono": "☕ Підтримати в Mono",
        "btn.support_bmac": "☕ Buy me a coffee",
        "btn.feedback_dev": "✉️ Написати розробнику",
        "trip.pick_currency": "💱 Оберіть <b>валюту</b> для цієї поїздки / події (суми витрат будуть у ній).",
        "trip.ask_name": "🆕 Напишіть <b>назву поїздки або події</b> одним повідомленням у чат.",
        "trip.name_empty": "❌ Назва не може бути порожньою.",
        "trip.cancelled": "❌ Створення поїздки / події скасовано.",
        "trip.cancel_short": "Скасовано",
        "trip.active_exists": "Уже є активна поїздка чи подія. Завершіть її спочатку.",
        "trip.created": "✅ Поїздку / подію «{name}» створено!\nДодавайте витрати через меню або /spent.",
        "trip.default_name": "Поїздка / подія",
        "here.ok": (
            "✅ Вас додано до списку учасників для поділу витрат у цій групі.\n"
            "Якщо когось немає в списку при витраті — нехай теж надішле <code>/here</code> сюди."
        ),
        "exp.enter_amount": "💸 Введіть <b>суму</b> витрати (наприклад <code>100</code> або <code>50.25</code>).",
        "exp.enter_amount_hint": (
            "💸 Введіть <b>суму</b> витрати (наприклад <code>100</code> або <code>50.25</code>). "
            "Можна одним рядком: <code>100 кава</code> або <code>Кава 100</code>.\n"
            "Або одним рядком: <code>/spent 250.50 Кава</code>.\n"
            "Щоб вийти і не заважати чату: <code>/cancel</code> або <code>/menu</code>."
        ),
        "exp.bad_amount": "❌ Надішліть лише суму числом, наприклад <code>100</code> або <code>50.25</code> (або <code>/cancel</code>).",
        "exp.abandon_casual": (
            "💬 Схоже, ви просто спілкуєтесь у чаті. <b>Майстер витрати вимкнено.</b>\n"
            "Щоб додати витрату знову — кнопка «Додати витрату» або <code>/spent</code>. "
            "Підказка: під час кроків бота можна завжди надіслати <code>/cancel</code>."
        ),
        "wizard.cancelled_cmd": "✅ Майстер бота вимкнено — можете далі писати в чат.",
        "wizard.no_active": "ℹ️ Немає незавершеного кроку бота.",
        "exp.ask_desc": (
            "📝 Напишіть короткий опис витрати одним повідомленням.\n"
            "Або надішліть <code>-</code>, щоб залишити без опису."
        ),
        "exp.no_chat": "💬 Спочатку напишіть повідомлення в чаті, щоб я бачив учасників.",
        "exp.no_trip": "🧾 Немає активної поїздки чи події. Створіть її через меню.",
        "exp.no_members_db": "👥 У чаті ще немає учасників у моїй базі. Напишіть повідомлення в групі.",
        "exp.split_hint": (
            "\n\nОберіть, між ким ділити суму, або «Розділити на всіх»."
            "\n\n<i>Немає людини в списку? Нехай надішле <code>/here</code> або повідомлення, "
            "потім натисніть <b>«Оновити список»</b>. Адмінів підтягую автоматично.</i>"
        ),
        "exp.split_all": "🚀 Розділити на всіх",
        "exp.refresh": "🔄 Оновити список",
        "exp.confirm": "💳 Підтвердити",
        "exp.wizard_cancelled": "❌ Скасовано.",
        "exp.not_for_you": "⛔️ Це меню не для вас.",
        "exp.chat_not_found": "Чат не знайдено.",
        "exp.pick_one": "Оберіть хоча б одного учасника.",
        "exp.user_not_found": "Користувача не знайдено.",
        "exp.done": "Готово!",
        "exp.list_refreshed": "Список оновлено",
        "exp.saved": "✅ Збережено витрату {amount}",
        "exp.payer": "👤 Платник: {name}",
        "exp.cancelled_flow": "❌ Введення витрати скасовано.",
        "exp.no_active_cmd": "🧾 Немає активної поїздки чи події. Створіть її через меню або <code>/new_trip</code>.",
        "exp.need_chat_trip": "💬 Надішліть будь-яке повідомлення в чат, щоб я запам’ятав учасників, і спробуйте знову.",
        "exp.active_exists_reply": "⚠️ У цьому чаті вже є активна поїздка чи подія. Завершіть її через меню або /finish_trip.",
        "exp.profile_missing": "❌ Не вдалося знайти ваш профіль. Напишіть будь-яке повідомлення й повторіть спробу.",
        "menu.no_trip_expense": "Немає активної поїздки чи події. Спочатку створіть її через «Нова поїздка / подія».",
        "status.no_chat": "💬 Немає даних про чат. Напишіть повідомлення в групі.",
        "status.no_trip": "🧾 Немає активної поїздки чи події. Створіть її через меню або /new_trip",
        "status.title": "🧾 <b>{name}</b> <i>(поїздка чи подія — як назвете)</i>",
        "status.total": "💰 Загалом витрачено: <b>{total}</b>",
        "status.balances": "Баланси (заплатив − має віддати):",
        "finish.no_chat": "💬 Немає даних про чат.",
        "finish.no_trip": "🏁 Немає активної поїздки чи події.",
        "finish.forbidden": "⛔️ Завершити поїздку чи подію можуть лише той, хто її створив, або адміністратори групи.",
        "finish.done": "🏁 Поїздку / подію «{name}» завершено!",
        "finish.balanced": "✅ Розрахунки збалансовані — переказів не потрібно.",
        "finish.transfers": "Мінімальні перекази:",
        "user.default": "Користувач",
        "onboarding.welcome": (
            "👋 Привіт! Я <b>Bill Splitter</b> — допоможу розібратися з грошима без зайвих суперечок після поїздок і подій.\n\n"
            "Зробіть мене <b>адміном</b> з доступом до повідомлень — так я швидше підтягну адмінів у список для поділу. "
            "Решта з’явиться, коли люди <b>напишуть у чат</b> (якщо я бачу повідомлення) або один раз <code>/here</code>.\n\n"
            "Тисніть кнопки нижче, пишіть <code>/menu</code> / <code>/start</code> або згадайте мене через <code>@</code>."
        ),
        "help.block": (
            "❓ <b>Як працює Bill Splitter?</b>\n\n"
            "Я допомагаю компанії друзів вести спільний бюджет. Більше не треба записувати борги в нотатки "
            "чи рахувати на калькуляторі!\n\n"
            "🏁 <b>З чого почати?</b>\n\n"
            "Створіть подію: <b>«Нова поїздка»</b> <i>(одна активна на чат)</i>.\n\n"
            "Записуйте витрати: <b>«Додати витрату»</b>.\n"
            "Я запитаю суму, опис та на кого поділити чек.\n\n"
            "Дивіться баланс: <b>«Статус»</b> покаже, хто «в плюсі», а хто «в мінусі».\n\n"
            "Розрахуйтесь: <b>«Завершити»</b>. Я видам список мінімальних переказів: хто, кому і скільки має скинути.\n\n"
            "👥 <b>Хто в списку?</b>\n"
            "Щоб я міг порахувати вашу частку, я маю вас «побачити». Натисніть <code>/here</code> або просто напишіть "
            "будь-що у чат.\n\n"
            "🛠 <b>Короткі команди для профі</b>\n"
            "<code>/spent 250 Кава</code> — швидка витрата одним рядком.\n"
            "<code>/status</code> — актуальні баланси.\n"
            "<code>/finish_trip</code> — фінальний розрахунок.\n"
            "<code>/cancel</code> — вийти з кроків бота, якщо завис «на питанні».\n\n"
        ),
        "help.support_mono": (
            "☕️ <b>Підтримка</b>\n"
            "Бот повністю безкоштовний. Але якщо я закрив ваш фінансовий «гештальт» — буду вдячний за каву "
            "розробнику одним тапом нижче! 👇"
        ),
        "help.support_generic": (
            "☕️ <b>Підтримка</b>\n"
            "Бот повністю безкоштовний. Приємних спільних поїздок і подій!"
        ),
        "coffee.block": (
            "☕️ <b>Пригостити розробника кавою</b>\n\n"
            "Якщо цей бот допоміг вам швидко розібратися з фінансами та зберегти нерви (і дружбу) "
            "після поїздки чи події — буду вдячний за віртуальну каву! Це мотивує додавати нові фічі та підтримувати сервер."
        ),
        "coffee.link_mono": "Mono",
        "coffee.link_bmac": "Buy Me a Coffee",
    },
    "en": {
        "menu.caption": (
            "👋 Hi! I’m your <b>Bill Splitter</b>.\n"
            "I’ll help your group sort out money without awkward arguments. "
            "For me to see everyone who should split costs, ask them to post in this chat or send <code>/here</code> once.\n\n"
            "<b>How to start?</b>\n"
            "1️⃣ Create a <b>New trip / event</b>.\n"
            "2️⃣ Add expenses with <b>Add expense</b>.\n"
            "3️⃣ When you’re done, tap <b>Settle</b> — I’ll show who owes whom.\n\n"
            "Pick an action below, mention me with @, or use <code>/menu</code>.\n\n"
            "<i>During the expense wizard: <code>/cancel</code> exits so you can chat freely.</i>"
        ),
        "btn.new_trip": "🆕 New trip / event",
        "btn.add_expense": "💸 Add expense",
        "btn.status": "📊 Status",
        "btn.finish": "🏁 Settle debts",
        "btn.help": "❓ Help",
        "btn.cancel": "❌ Cancel",
        "btn.stop_wizard": "🛑 Exit wizard",
        "btn.back_actions": "🔙 Back to actions",
        "btn.support_mono": "☕ Support via Mono",
        "btn.support_bmac": "☕ Buy me a coffee",
        "btn.feedback_dev": "✉️ Message the developer",
        "trip.pick_currency": "💱 Choose the <b>currency</b> for this trip or event (all amounts will use it).",
        "trip.ask_name": "🆕 Send the <b>name of the trip or event</b> in one message.",
        "trip.name_empty": "❌ The name can’t be empty.",
        "trip.cancelled": "❌ Trip / event creation cancelled.",
        "trip.cancel_short": "Cancelled",
        "trip.active_exists": "There is already an active trip or event. Finish it first.",
        "trip.created": "✅ Trip / event «{name}» created!\nAdd expenses from the menu or /spent.",
        "trip.default_name": "Trip / event",
        "here.ok": (
            "✅ You’re on the list for splitting expenses in this group.\n"
            "If someone is missing when adding an expense, ask them to send <code>/here</code> here too."
        ),
        "exp.enter_amount": "💸 Enter the expense <b>amount</b> (e.g. <code>100</code> or <code>50.25</code>).",
        "exp.enter_amount_hint": (
            "💸 Enter the expense <b>amount</b> (e.g. <code>100</code> or <code>50.25</code>). "
            "One line works too: <code>100 coffee</code> or <code>Coffee 100</code>.\n"
            "Or in one line: <code>/spent 25.50 Coffee</code>.\n"
            "To exit and not spam the group: <code>/cancel</code> or <code>/menu</code>."
        ),
        "exp.bad_amount": "❌ Send just a number, e.g. <code>100</code> or <code>50.25</code> (or <code>/cancel</code>).",
        "exp.abandon_casual": (
            "💬 Looks like you’re chatting. <b>The expense wizard is closed.</b>\n"
            "To add an expense again — use <b>Add expense</b> or <code>/spent</code>. "
            "Tip: during any bot step you can send <code>/cancel</code>."
        ),
        "wizard.cancelled_cmd": "✅ Bot wizard cleared — you can keep chatting.",
        "wizard.no_active": "ℹ️ No unfinished bot step right now.",
        "exp.ask_desc": (
            "📝 Send a short description in one message.\n"
            "Or send <code>-</code> to skip."
        ),
        "exp.no_chat": "💬 Send any message in the chat first so I know who’s here.",
        "exp.no_trip": "🧾 No active trip or event. Create one from the menu.",
        "exp.no_members_db": "👥 No members in my database yet. Post in the group first.",
        "exp.split_hint": (
            "\n\nChoose who splits the total, or <b>Split among everyone</b>."
            "\n\n<i>Someone missing? They can send <code>/here</code> or a message, then tap <b>Refresh list</b>. "
            "Admins are synced automatically.</i>"
        ),
        "exp.split_all": "🚀 Split among everyone",
        "exp.refresh": "🔄 Refresh list",
        "exp.confirm": "💳 Confirm",
        "exp.wizard_cancelled": "❌ Cancelled.",
        "exp.not_for_you": "⛔️ This menu isn’t for you.",
        "exp.chat_not_found": "Chat not found.",
        "exp.pick_one": "Pick at least one person.",
        "exp.user_not_found": "User not found.",
        "exp.done": "Done!",
        "exp.list_refreshed": "List updated",
        "exp.saved": "✅ Saved expense {amount}",
        "exp.payer": "👤 Paid by: {name}",
        "exp.cancelled_flow": "❌ Expense entry cancelled.",
        "exp.no_active_cmd": "🧾 No active trip or event. Create one from the menu or <code>/new_trip</code>.",
        "exp.need_chat_trip": "💬 Send any message in the chat so I remember members, then try again.",
        "exp.active_exists_reply": "⚠️ This chat already has an active trip or event. Finish it from the menu or /finish_trip.",
        "exp.profile_missing": "❌ Couldn’t find your profile. Send any message and try again.",
        "menu.no_trip_expense": "No active trip or event. Create one with <b>New trip / event</b> first.",
        "status.no_chat": "💬 No chat data yet. Send a message in the group.",
        "status.no_trip": "🧾 No active trip or event. Create one from the menu or /new_trip",
        "status.title": "🧾 <b>{name}</b> <i>(trip or event)</i>",
        "status.total": "💰 Total spent: <b>{total}</b>",
        "status.balances": "Balances (paid − your share):",
        "finish.no_chat": "💬 No chat data.",
        "finish.no_trip": "🏁 No active trip or event.",
        "finish.forbidden": "⛔️ Only the creator or group admins can finish the trip or event.",
        "finish.done": "🏁 Trip / event «{name}» closed!",
        "finish.balanced": "✅ All settled — no transfers needed.",
        "finish.transfers": "Minimum transfers:",
        "user.default": "User",
        "onboarding.welcome": (
            "👋 Hi! I’m <b>Bill Splitter</b> — I help groups settle money without the awkwardness.\n\n"
            "Make me an <b>admin</b> with message access so I can pull admins into the split list faster. "
            "Everyone else appears when they <b>post in chat</b> (if I can see messages) or send <code>/here</code> once.\n\n"
            "Use the buttons below, <code>/menu</code> / <code>/start</code>, or mention me with <code>@</code>."
        ),
        "help.block": (
            "❓ <b>How Bill Splitter works</b>\n\n"
            "I help friend groups track a shared budget — no more notes app or calculator debates.\n\n"
            "🏁 <b>Where to start?</b>\n\n"
            "Create an event: <b>New trip / event</b> <i>(one active per chat)</i>.\n\n"
            "Log spending: <b>Add expense</b>.\n"
            "I’ll ask for amount, description, and who splits the bill.\n\n"
            "Check balances: <b>Status</b> shows who’s up and who’s down.\n\n"
            "Settle up: <b>Settle debts</b>. I’ll list the smallest set of transfers.\n\n"
            "👥 <b>Who’s on the list?</b>\n"
            "I need to “see” someone to count their share. They can send <code>/here</code> or any message in the chat.\n\n"
            "🛠 <b>Quick commands</b>\n"
            "<code>/spent 250 Coffee</code> — quick expense in one line.\n"
            "<code>/status</code> — current balances.\n"
            "<code>/finish_trip</code> — final settlement.\n"
            "<code>/cancel</code> — leave the bot wizard if you’re stuck mid-flow.\n\n"
        ),
        "help.support_mono": (
            "☕️ <b>Support</b>\n"
            "The bot is free. If it saved you a headache, a virtual coffee for the developer below is appreciated! 👇"
        ),
        "help.support_bmac": (
            "☕️ <b>Support</b>\n"
            "The bot is free. If it helped, you can thank the developer with a coffee — tap below! 👇"
        ),
        "help.support_generic": (
            "☕️ <b>Support</b>\n"
            "The bot is free. Enjoy your trips and events!"
        ),
        "coffee.block": (
            "☕️ <b>Buy the developer a coffee</b>\n\n"
            "If this bot saved you time and awkward money talks — thanks for a virtual coffee! "
            "It helps keep the bot running and improving."
        ),
        "coffee.link_mono": "Mono",
        "coffee.link_bmac": "Buy Me a Coffee",
    },
}
