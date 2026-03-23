from __future__ import annotations

from aiogram.enums import ChatMemberStatus
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models import Chat, Trip, User


async def chat_by_tg(session: AsyncSession, tg_chat_id: int) -> Chat | None:
    res = await session.execute(select(Chat).where(Chat.tg_id == tg_chat_id))
    return res.scalar_one_or_none()


async def user_by_tg(session: AsyncSession, tg_user_id: int) -> User | None:
    res = await session.execute(select(User).where(User.tg_id == tg_user_id))
    return res.scalar_one_or_none()


async def active_trip(session: AsyncSession, chat_internal_id: int) -> Trip | None:
    res = await session.execute(
        select(Trip)
        .options(selectinload(Trip.created_by))
        .where(Trip.chat_id == chat_internal_id, Trip.is_active.is_(True))
        .limit(1)
    )
    return res.scalar_one_or_none()


async def is_user_group_admin(bot, chat_id: int, user_id: int) -> bool:
    m = await bot.get_chat_member(chat_id, user_id)
    return m.status in (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR)


async def is_group_admin(message: Message) -> bool:
    return await is_user_group_admin(message.bot, message.chat.id, message.from_user.id)
