from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu, WizardCancel


def main_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🆕 Нова поїздка / подія", callback_data=MainMenu(act="nt").pack()),
                InlineKeyboardButton(text="💸 Додати витрату", callback_data=MainMenu(act="ex").pack()),
            ],
            [
                InlineKeyboardButton(text="📊 Статус", callback_data=MainMenu(act="st").pack()),
                InlineKeyboardButton(text="🏁 Завершити", callback_data=MainMenu(act="ft").pack()),
            ],
            [InlineKeyboardButton(text="❓ Допомога", callback_data=MainMenu(act="hp").pack())],
        ]
    )


def wizard_cancel_row() -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text="❌ Скасувати", callback_data=WizardCancel().pack())]
