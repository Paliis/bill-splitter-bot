from __future__ import annotations

from aiogram.types import User as TgUser
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models import Chat, ChatMember, User


async def _upsert_user(session: AsyncSession, tg_user: TgUser) -> User:
    stmt = select(User).where(User.tg_id == tg_user.id)
    res = await session.execute(stmt)
    row = res.scalar_one_or_none()
    name = (tg_user.full_name or tg_user.first_name or "").strip() or "Користувач"
    uname = tg_user.username
    if row:
        row.full_name = name
        row.username = uname
        await session.flush()
        return row
    u = User(tg_id=tg_user.id, full_name=name, username=uname)
    session.add(u)
    await session.flush()
    return u


async def _upsert_chat(session: AsyncSession, tg_chat_id: int, title: str) -> Chat:
    stmt = select(Chat).where(Chat.tg_id == tg_chat_id)
    res = await session.execute(stmt)
    row = res.scalar_one_or_none()
    if row:
        row.title = title or row.title
        await session.flush()
        return row
    c = Chat(tg_id=tg_chat_id, title=title or "")
    session.add(c)
    await session.flush()
    return c


async def _ensure_member(session: AsyncSession, user_id: int, chat_id: int) -> None:
    stmt = select(ChatMember).where(ChatMember.user_id == user_id, ChatMember.chat_id == chat_id)
    res = await session.execute(stmt)
    if res.scalar_one_or_none():
        return
    session.add(ChatMember(user_id=user_id, chat_id=chat_id))
    await session.flush()


async def track_user_in_chat(session: AsyncSession, tg_user: TgUser, tg_chat_id: int, title: str) -> None:
    user = await _upsert_user(session, tg_user)
    chat = await _upsert_chat(session, tg_chat_id, title)
    await _ensure_member(session, user.id, chat.id)
