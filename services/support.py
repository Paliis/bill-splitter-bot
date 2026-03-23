from __future__ import annotations

import html
import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu


def support_mono_url() -> str:
    return (os.getenv("SUPPORT_MONO_URL") or "").strip()


def support_feedback_url() -> str:
    """Посилання для фідбеку (наприклад https://t.me/username)."""
    return (os.getenv("SUPPORT_FEEDBACK_URL") or "").strip()


def _help_support_paragraph_html() -> str:
    if support_mono_url():
        return (
            "☕️ <b>Підтримка</b>\n"
            "Бот повністю безкоштовний. Але якщо я закрив ваш фінансовий «гештальт» — буду вдячний за каву "
            "розробнику одним тапом нижче! 👇"
        )
    return (
        "☕️ <b>Підтримка</b>\n"
        "Бот повністю безкоштовний. Приємних спільних поїздок і подій!"
    )


def help_text_html() -> str:
    core = (
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
        "<code>/finish_trip</code> — фінальний розрахунок.\n\n"
    )
    return core + _help_support_paragraph_html()


def coffee_footer_html() -> str:
    block = (
        "☕️ <b>Пригостити розробника кавою</b>\n\n"
        "Якщо цей бот допоміг вам швидко розібратися з фінансами та зберегти нерви (і дружбу) "
        "після поїздки чи події — буду вдячний за віртуальну каву! Це мотивує додавати нові фічі та підтримувати сервер."
    )
    mono = support_mono_url()
    if not mono:
        return block
    return "\n".join(
        [
            block,
            "",
            f'• <a href="{html.escape(mono, quote=True)}">Mono</a>',
        ]
    )


def help_reply_markup() -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    if u := support_mono_url():
        rows.append([InlineKeyboardButton(text="☕ Підтримати в Mono", url=u)])
    if u := support_feedback_url():
        rows.append([InlineKeyboardButton(text="✉️ Написати розробнику", url=u)])
    rows.append([InlineKeyboardButton(text="🔙 До вибору дій", callback_data=MainMenu(act="mn").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)
