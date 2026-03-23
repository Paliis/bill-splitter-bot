from __future__ import annotations

import html
from decimal import Decimal

from models import User
from services.i18n import Locale, format_currency_amount, tr


def money_uah(value: Decimal) -> str:
    """Зворотна сумісність: лише UAH + український підпис."""
    q = value.quantize(Decimal("0.01"))
    return format_currency_amount("uk", f"{q:.2f}", "UAH")


def format_trip_money(value: Decimal, currency_code: str, locale: Locale) -> str:
    q = value.quantize(Decimal("0.01"))
    return format_currency_amount(locale, f"{q:.2f}", currency_code)


def user_mention_html(user: User, locale: Locale = "uk") -> str:
    name = html.escape(user.full_name or tr(locale, "user.default"))
    if user.username:
        un = html.escape(user.username)
        return f"@{un}"
    return f'<a href="tg://user?id={user.tg_id}">{name}</a>'


def truncate_label(text: str, max_len: int = 40) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"
