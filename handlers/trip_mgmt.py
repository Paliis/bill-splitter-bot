from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from formatting import format_trip_money, user_mention_html
from handlers.db_utils import active_trip, chat_by_tg, is_user_group_admin, user_by_tg
from models import Trip, User
from services.balances import compute_trip_net_by_user, list_chat_member_balances, trip_total_spent
from services.i18n import Locale, tr
from services.settlement import greedy_minimal_transfers, normalize_trip_nets_to_zero_sum
from services.support import coffee_footer_html
from services.sync_admins import sync_group_admins

router = Router(name="trip_mgmt")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


async def send_group_status(message: Message, session: AsyncSession, locale: Locale) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply(tr(locale, "status.no_chat"))
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply(tr(locale, "status.no_trip"))
        return
    total = await trip_total_spent(session, trip.id)
    rows = await list_chat_member_balances(session, trip)
    nm = html.escape(trip.name or "")
    cc = trip.currency or "UAH"
    total_s = format_trip_money(total, cc, locale)
    lines = [
        tr(locale, "status.title", name=nm),
        tr(locale, "status.total", total=total_s),
        "",
        tr(locale, "status.balances"),
    ]
    for u, net in rows:
        sign = "+" if net > 0 else ""
        lines.append(
            f"• {user_mention_html(u, locale)}: <b>{sign}{format_trip_money(net, cc, locale)}</b>"
        )
    await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)


async def send_group_finish(
    message: Message,
    session: AsyncSession,
    locale: Locale,
    *,
    actor_tg_id: int | None = None,
) -> None:
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply(tr(locale, "finish.no_chat"))
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply(tr(locale, "finish.no_trip"))
        return
    uid = actor_tg_id if actor_tg_id is not None else message.from_user.id
    creator_tg = trip.created_by.tg_id if trip.created_by else None
    allowed = (creator_tg is not None and creator_tg == uid) or await is_user_group_admin(
        message.bot, message.chat.id, uid
    )
    if not allowed:
        await message.reply(tr(locale, "finish.forbidden"))
        return

    nets = await compute_trip_net_by_user(session, trip.id)
    nets = normalize_trip_nets_to_zero_sum(nets)
    transfers = greedy_minimal_transfers(nets)

    trip.is_active = False
    await session.flush()

    nm = html.escape(trip.name or "")
    cc = trip.currency or "UAH"
    head = tr(locale, "finish.done", name=nm)
    coffee = coffee_footer_html(locale)

    if not transfers:
        body = f"{head}\n{tr(locale, 'finish.balanced')}"
        if coffee:
            body = f"{body}\n\n{coffee}"
        await message.reply(body, parse_mode=ParseMode.HTML)
        return

    user_by_id: dict[int, User] = {}
    for tuid in {t[0] for t in transfers} | {t[1] for t in transfers}:
        res = await session.execute(select(User).where(User.id == tuid))
        u = res.scalar_one_or_none()
        if u:
            user_by_id[tuid] = u

    lines = [head, "", tr(locale, "finish.transfers"), ""]
    for du, cu, amt in transfers:
        du_u = user_by_id.get(du)
        cu_u = user_by_id.get(cu)
        if not du_u or not cu_u:
            continue
        lines.append(
            f"{user_mention_html(du_u, locale)} → {user_mention_html(cu_u, locale)}: "
            f"<b>{format_trip_money(amt, cc, locale)}</b>"
        )
    body = "\n".join(lines)
    if coffee:
        body = f"{body}\n\n{coffee}"
    await message.reply(body, parse_mode=ParseMode.HTML)


async def try_create_trip(
    message: Message,
    session: AsyncSession,
    name: str,
    *,
    currency: str = "UAH",
    locale: Locale,
) -> bool:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply(tr(locale, "exp.need_chat_trip"))
        return False
    if await active_trip(session, chat.id):
        await message.reply(tr(locale, "exp.active_exists_reply"))
        return False
    nm = name.strip() or tr(locale, "trip.default_name")
    actor = await user_by_tg(session, message.from_user.id)
    if not actor:
        await message.reply(tr(locale, "exp.profile_missing"))
        return False
    cur = (currency or "UAH").upper()
    trip = Trip(chat_id=chat.id, name=nm, currency=cur, is_active=True, created_by_id=actor.id)
    session.add(trip)
    await session.flush()
    safe = html.escape(nm)
    await message.reply(
        tr(locale, "trip.created", name=safe),
        parse_mode=ParseMode.HTML,
    )
    return True


@router.message(Command("new_trip"))
async def cmd_new_trip(
    message: Message,
    command: CommandObject,
    session: AsyncSession,
    locale: Locale,
) -> None:
    name = (command.args or "").strip() or tr(locale, "trip.default_name")
    cur = "UAH" if locale == "uk" else "USD"
    await try_create_trip(message, session, name, currency=cur, locale=locale)


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession, locale: Locale) -> None:
    await send_group_status(message, session, locale)


@router.message(Command("finish_trip"))
async def cmd_finish_trip(message: Message, session: AsyncSession, locale: Locale) -> None:
    await send_group_finish(message, session, locale, actor_tg_id=None)
