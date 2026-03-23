from __future__ import annotations

import html
import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu


def support_mono_url() -> str:
    return (os.getenv("SUPPORT_MONO_URL") or "").strip()


def support_buymeacoffee_url() -> str:
    return (os.getenv("SUPPORT_BUYMEACOFFEE_URL") or "").strip()


def help_text_html() -> str:
    return (
        "❓ <b>Допомога — Bill Splitter</b>\n\n"
        "<b>Навіщо бот</b>\n"
        "Рахує спільні витрати в групі: хто скільки заплатив, яка ваша «чиста» позиція "
        "і хто кому має доплатити після поїздки, вечірки чи будь-якого спільного періоду.\n\n"
        "<b>Як користуватись</b>\n"
        "• <b>Нова поїздка / подія</b> — один активний період на чат; дайте йому назву.\n"
        "• <b>Додати витрату</b> — сума → опис → оберіть, між ким ділити (або «на всіх»). "
        "Платник — той, хто натискає «Підтвердити».\n"
        "• <code>/spent 250.50 Кава</code> — те саме одним рядком; або просто <code>/spent</code> "
        "і далі кроки як з кнопки.\n"
        "• <b>Статус</b> — загальна сума та баланси: <i>заплатив − ваша частка у витратах</i>. "
        "У сумі по всіх має вийти нуль.\n"
        "• <b>Завершити</b> — закриває подію; бот показує мінімальний набір переказів «хто кому».\n\n"
        "<b>Учасники</b>\n"
        "Telegram не дає боту повний список учасників групи. У списку для поділу — <b>адміни</b> "
        "(підтягуються автоматично) і ті, кого бот уже «бачив»: повідомлення в чаті, редагування, "
        "натискання кнопок меню в групі. Якщо в BotFather увімкнено <b>Group Privacy</b>, звичайні "
        "повідомлення бот може не бачити — тоді надійний спосіб зареєструватись: один раз "
        "<code>/here</code> (команди до бота доходять завжди).\n\n"
        "<b>Хто може завершити подію</b>\n"
        "Той, хто її створив, або адміністратори групи.\n\n"
        "<b>Команди</b>\n"
        "<code>/menu</code>, <code>/new_trip</code>, <code>/spent</code>, <code>/status</code>, "
        "<code>/finish_trip</code>, <code>/help</code>, <code>/here</code> (зареєструватись у списку учасників)\n\n"
        "<b>Підтримка</b>\n"
        "Після завершення події бот може додати блок «віртуальна кава». "
        "Кнопки <b>Mono</b> / <b>Buy Me a Coffee</b> під цим повідомленням з’являються лише якщо "
        "на сервері бота задано відповідні посилання у змінних середовища (локально — у <code>.env</code>, "
        "на хостингу — у налаштуваннях сервісу). Якщо кнопок немає — змінні не задані на цьому запуску."
    )


def coffee_footer_html() -> str:
    block = (
        "☕️ <b>Пригостити розробника кавою</b>\n\n"
        "Якщо цей бот допоміг вам швидко розібратися з фінансами та зберегти нерви (і дружбу) "
        "після поїздки чи події — буду вдячний за віртуальну каву! Це мотивує додавати нові фічі та підтримувати сервер."
    )
    mono = support_mono_url()
    bmac = support_buymeacoffee_url()
    if not mono and not bmac:
        return block
    parts = [block, ""]
    if mono:
        parts.append(f'• <a href="{html.escape(mono, quote=True)}">Mono</a>')
    if bmac:
        parts.append(f'• <a href="{html.escape(bmac, quote=True)}">Buy Me a Coffee</a>')
    return "\n".join(parts)


def help_reply_markup() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if u := support_mono_url():
        rows.append([InlineKeyboardButton(text="☕ Mono", url=u)])
    if u := support_buymeacoffee_url():
        rows.append([InlineKeyboardButton(text="☕ Buy Me a Coffee", url=u)])
    rows.append([InlineKeyboardButton(text="📋 До меню", callback_data=MainMenu(act="mn").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)
