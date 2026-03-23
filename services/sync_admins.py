from __future__ import annotations

from aiogram import Bot
from aiogram.exceptions import TelegramBadRequest
from sqlalchemy.ext.asyncio import AsyncSession

from services.membership import track_user_in_chat


async def sync_group_admins(bot: Bot, session: AsyncSession, tg_chat_id: int) -> None:
    try:
        admins = await bot.get_chat_administrators(chat_id=tg_chat_id)
    except TelegramBadRequest:
        return
    title = ""
    try:
        ch = await bot.get_chat(chat_id=tg_chat_id)
        title = ch.title or ""
    except TelegramBadRequest:
        pass
    for cm in admins:
        u = cm.user
        if u.is_bot:
            continue
        await track_user_in_chat(session, u, tg_chat_id, title)
