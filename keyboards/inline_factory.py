from __future__ import annotations

from typing import Iterable, Sequence, Set

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from formatting import truncate_label
from handlers.callback_data import ExpCancel, ExpConfirm, ExpSplitAll, ExpToggle


def expense_participants_kb(
    members: Sequence[tuple[int, str]],
    selected: Set[int],
) -> InlineKeyboardMarkup:
    rows: list[list[InlineKeyboardButton]] = []
    rows.append(
        [InlineKeyboardButton(text="🚀 Розділити на всіх", callback_data=ExpSplitAll().pack())]
    )
    for uid, label in members:
        mark = "✅" if uid in selected else " "
        text = f"[{mark}] {truncate_label(label, 36)}"
        rows.append([InlineKeyboardButton(text=text, callback_data=ExpToggle(user_id=uid).pack())])
    rows.append(
        [
            InlineKeyboardButton(text="💳 Підтвердити", callback_data=ExpConfirm().pack()),
            InlineKeyboardButton(text="❌ Скасувати", callback_data=ExpCancel().pack()),
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def member_labels(users: Iterable) -> list[tuple[int, str]]:
    out: list[tuple[int, str]] = []
    for u in users:
        label = u.full_name or "Користувач"
        if u.username:
            label = f"{label} (@{u.username})"
        out.append((int(u.id), label))
    out.sort(key=lambda x: x[1].lower())
    return out
