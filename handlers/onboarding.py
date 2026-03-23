from __future__ import annotations

import asyncio
import logging
import time

from aiogram import Bot, F, Router
from aiogram.enums import ChatMemberStatus, ParseMode
from aiogram.types import ChatMemberUpdated, Message
from sqlalchemy.ext.asyncio import AsyncSession

from keyboards.main_menu import main_menu_kb
from services.sync_admins import sync_group_admins

router = Router(name="onboarding")

_ACTIVE = frozenset(
    {
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.CREATOR,
    }
)

# Після відправки вітання — не дублювати (my_chat_member + service message).
_last_onboarding_mono: dict[int, float] = {}
_DEBOUNCE_AFTER_SEND_SEC = 15.0

# Пауза перед вітанням: кілька апдейтів підряд (наприклад, багато new_chat_members) зливаються в одне повідомлення.
_WELCOME_DELAY_SEC = 3.5
_WELCOME_TASKS: dict[int, asyncio.Task[None]] = {}
logger = logging.getLogger(__name__)


def _welcome_text() -> str:
    return (
        "👋 Привіт! Я <b>Bill Splitter</b> — підкажу, хто скільки витратив і хто кому винен, "
        "щоб після спільних поїздок чи подій не рахувати все на пальцях.\n\n"
        "<b>Два нюанси</b> (і все)\n"
        "• Зробіть мене <b>адміном</b> з доступом до повідомлень — так я сам підтягну <b>адмінів</b> у список для поділу.\n"
        "• Решту людей додам, коли вони <b>напишуть у чат</b> (якщо я бачу повідомлення), або один раз <code>/here</code>, "
        "або їх <b>додадуть у групу</b>.\n\n"
        "<b>Як користуватись</b>\n"
        "Тисніть кнопки нижче, або <code>/menu</code> / <code>/start</code>, або просто згадайте мене через <code>@</code>… у повідомленні.\n\n"
        "Як любите текстом: <code>/new_trip</code>, <code>/spent</code>, <code>/status</code>, <code>/finish_trip</code>, <code>/here</code>"
    )


def _mark_onboarding(chat_id: int) -> bool:
    """Повертає True, якщо можна надіслати вітання (не дубль за короткий час після попереднього)."""
    now = time.monotonic()
    prev = _last_onboarding_mono.get(chat_id, 0.0)
    if now - prev < _DEBOUNCE_AFTER_SEND_SEC:
        return False
    _last_onboarding_mono[chat_id] = now
    return True


def _cancel_pending_welcome(chat_id: int) -> None:
    t = _WELCOME_TASKS.get(chat_id)
    if t is not None and not t.done():
        t.cancel()


def _clear_welcome_task_slot(chat_id: int, task: asyncio.Task[None] | None) -> None:
    if task is not None and _WELCOME_TASKS.get(chat_id) is task:
        _WELCOME_TASKS.pop(chat_id, None)


async def _run_onboarding(bot: Bot, session: AsyncSession, chat_id: int, reply_to: Message | None = None) -> None:
    await sync_group_admins(bot, session, chat_id)
    text = _welcome_text()
    kb = main_menu_kb()
    if reply_to:
        await reply_to.reply(text, parse_mode=ParseMode.HTML, reply_markup=kb)
    else:
        await bot.send_message(chat_id=chat_id, text=text, parse_mode=ParseMode.HTML, reply_markup=kb)


async def _delayed_welcome(bot: Bot, chat_id: int, reply_to: Message | None) -> None:
    me = asyncio.current_task()
    try:
        await asyncio.sleep(_WELCOME_DELAY_SEC)
    except asyncio.CancelledError:
        _clear_welcome_task_slot(chat_id, me)
        raise
    try:
        if not _mark_onboarding(chat_id):
            return
        from database import async_session_maker

        async with async_session_maker() as session:
            await _run_onboarding(bot, session, chat_id, reply_to=reply_to)
    except Exception:
        logger.exception("Onboarding welcome failed for chat_id=%s", chat_id)
        raise
    finally:
        _clear_welcome_task_slot(chat_id, me)


def _schedule_welcome(bot: Bot, chat_id: int, reply_to: Message | None) -> None:
    _cancel_pending_welcome(chat_id)
    task = asyncio.create_task(_delayed_welcome(bot, chat_id, reply_to))
    _WELCOME_TASKS[chat_id] = task


@router.my_chat_member(F.chat.type.in_({"group", "supergroup"}))
async def on_bot_joined_group(event: ChatMemberUpdated, bot: Bot, session: AsyncSession) -> None:
    me = await bot.get_me()
    if event.new_chat_member.user.id != me.id:
        return
    old = event.old_chat_member.status
    new = event.new_chat_member.status
    now_in = new in _ACTIVE
    was_in = old in _ACTIVE
    if not now_in or was_in:
        return
    _schedule_welcome(bot, event.chat.id, reply_to=None)


@router.message(F.chat.type.in_({"group", "supergroup"}), F.new_chat_members)
async def on_bot_in_new_members(message: Message, bot: Bot, session: AsyncSession) -> None:
    me = await bot.get_me()
    if not message.new_chat_members or not any(u.id == me.id for u in message.new_chat_members):
        return
    _schedule_welcome(bot, message.chat.id, reply_to=message)
