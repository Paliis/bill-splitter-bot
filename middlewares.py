from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser

from database import async_session_maker
from services.i18n import Locale, locale_from_telegram
from services.membership import track_user_in_chat


def _collect_group_users_from_update(update: Update) -> list[tuple[TgUser, int, str]]:
    """Пари (user, chat_id, title) для upsert у ChatMember; без дублікатів за (user.id, chat_id)."""
    out: list[tuple[TgUser, int, str]] = []
    seen: set[tuple[int, int]] = set()

    def add(u: TgUser | None, chat_id: int, title: str) -> None:
        if not u or u.is_bot:
            return
        key = (u.id, chat_id)
        if key in seen:
            return
        seen.add(key)
        out.append((u, chat_id, title))

    msg = update.message or update.edited_message
    if msg and msg.chat.type in ("group", "supergroup"):
        title = msg.chat.title or ""
        cid = msg.chat.id
        add(msg.from_user, cid, title)
        for nu in msg.new_chat_members or []:
            add(nu, cid, title)

    cb = update.callback_query
    if cb and cb.message and cb.message.chat.type in ("group", "supergroup"):
        title = cb.message.chat.title or ""
        cid = cb.message.chat.id
        add(cb.from_user, cid, title)

    return out


class TrackGroupMembersMiddleware(BaseMiddleware):
    """Upsert учасників з оновлень, де є from_user у групі (повідомлення, редагування, callback у чаті)."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            pairs = _collect_group_users_from_update(event)
            if pairs:
                async with async_session_maker() as track_session:
                    for tg_u, cid, title in pairs:
                        await track_user_in_chat(track_session, tg_u, cid, title)
                    await track_session.commit()
        return await handler(event, data)


class LocaleMiddleware(BaseMiddleware):
    """Мова з Telegram language_code: uk/ru → uk, інакше en."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        lang: str | None = None
        if isinstance(event, Update):
            if event.message and event.message.from_user:
                lang = event.message.from_user.language_code
            elif event.edited_message and event.edited_message.from_user:
                lang = event.edited_message.from_user.language_code
            elif event.callback_query and event.callback_query.from_user:
                lang = event.callback_query.from_user.language_code
            elif event.my_chat_member and event.my_chat_member.from_user:
                lang = event.my_chat_member.from_user.language_code
        loc: Locale = locale_from_telegram(lang)
        data["locale"] = loc
        return await handler(event, data)


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with async_session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            await session.commit()
            return result
