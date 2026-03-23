from __future__ import annotations

import html
from decimal import Decimal

from models import User


def money_uah(value: Decimal) -> str:
    q = value.quantize(Decimal("0.01"))
    return f"{q:.2f} грн"


def user_mention_html(user: User) -> str:
    name = html.escape(user.full_name or "Користувач")
    if user.username:
        un = html.escape(user.username)
        return f"@{un}"
    return f'<a href="tg://user?id={user.tg_id}">{name}</a>'


def truncate_label(text: str, max_len: int = 40) -> str:
    t = text.strip()
    if len(t) <= max_len:
        return t
    return t[: max_len - 1] + "…"
