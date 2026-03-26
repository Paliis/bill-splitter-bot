from __future__ import annotations

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from handlers.callback_data import MainMenu, TripCurrency, WizardCancel
from services.i18n import SUPPORTED_CURRENCIES, Locale, tr


def main_menu_kb(locale: Locale) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text=tr(locale, "btn.new_trip"), callback_data=MainMenu(act="nt").pack()),
                InlineKeyboardButton(text=tr(locale, "btn.add_expense"), callback_data=MainMenu(act="ex").pack()),
            ],
            [
                InlineKeyboardButton(text=tr(locale, "btn.status"), callback_data=MainMenu(act="st").pack()),
                InlineKeyboardButton(text=tr(locale, "btn.finish"), callback_data=MainMenu(act="ft").pack()),
            ],
            [
                InlineKeyboardButton(text=tr(locale, "btn.help"), callback_data=MainMenu(act="hp").pack()),
                InlineKeyboardButton(text=tr(locale, "btn.stop_wizard"), callback_data=MainMenu(act="cw").pack()),
            ],
        ]
    )


def wizard_cancel_row(locale: Locale) -> list[InlineKeyboardButton]:
    return [InlineKeyboardButton(text=tr(locale, "btn.cancel"), callback_data=WizardCancel().pack())]


def trip_currency_kb(locale: Locale) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    row: list[InlineKeyboardButton] = []
    for i, code in enumerate(SUPPORTED_CURRENCIES):
        row.append(InlineKeyboardButton(text=code, callback_data=TripCurrency(code=code).pack()))
        if len(row) >= 2:
            rows.append(row)
            row = []
    if row:
        rows.append(row)
    rows.append([InlineKeyboardButton(text=tr(locale, "btn.cancel"), callback_data=WizardCancel().pack())])
    return InlineKeyboardMarkup(inline_keyboard=rows)
