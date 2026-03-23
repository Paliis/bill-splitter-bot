from __future__ import annotations

import html
import os

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu


def support_mono_url() -> str:
    return (os.getenv("SUPPORT_MONO_URL") or "").strip()


def _help_support_section_html() -> str:
    if support_mono_url():
        return (
            "<b>Підтримка</b>\n"
            "Бот користується безкоштовно. Якщо він зекономив вам час і нерви — можна нагадати автору "
            "про каву одним тапом нижче (Mono). Після <b>завершення події</b> такий самий заклик інколи з’являється в кінці повідомлення."
        )
    return (
        "<b>Підтримка</b>\n"
        "Тут може з’явитись кнопка «кава» через <b>Mono</b>, коли власник бота додасть посилання "
        "<code>SUPPORT_MONO_URL</code> у змінних середовища — локально в <code>.env</code>, на хостингу в розділі Environment."
    )


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
        + _help_support_section_html()
    )


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
    rows.append([InlineKeyboardButton(text="🔙 До вибору дій", callback_data=MainMenu(act="mn").pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)
