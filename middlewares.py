from __future__ import annotations

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Update, User as TgUser

from database import async_session_maker
from services.membership import track_user_in_chat


class DbSessionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if isinstance(event, Update):
            msg = event.message or event.edited_message
            if msg and msg.chat.type in ("group", "supergroup"):
                title = msg.chat.title or ""
                cid = msg.chat.id
                members_to_track: list[TgUser] = []
                if msg.from_user:
                    members_to_track.append(msg.from_user)
                for nu in msg.new_chat_members or []:
                    if nu.is_bot:
                        continue
                    members_to_track.append(nu)
                if members_to_track:
                    async with async_session_maker() as track_session:
                        for tg_u in members_to_track:
                            await track_user_in_chat(track_session, tg_u, cid, title)
                        await track_session.commit()

        async with async_session_maker() as session:
            data["session"] = session
            try:
                result = await handler(event, data)
            except Exception:
                await session.rollback()
                raise
            await session.commit()
            return result
