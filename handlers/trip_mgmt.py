from __future__ import annotations

import html

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandObject
from aiogram.types import Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from formatting import money_uah, user_mention_html
from handlers.db_utils import active_trip, chat_by_tg, is_user_group_admin, user_by_tg
from models import Trip, User
from services.balances import compute_trip_net_by_user, list_chat_member_balances, trip_total_spent
from services.settlement import greedy_minimal_transfers, normalize_trip_nets_to_zero_sum
from services.support import coffee_footer_html
from services.sync_admins import sync_group_admins

router = Router(name="trip_mgmt")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))


async def send_group_status(message: Message, session: AsyncSession) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply("💬 Немає даних про чат. Напишіть повідомлення в групі.")
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply(
            "🧾 Немає активної поїздки чи події. Створіть її через меню або /new_trip"
        )
        return
    total = await trip_total_spent(session, trip.id)
    rows = await list_chat_member_balances(session, trip)
    nm = html.escape(trip.name or "")
    lines = [
        f"🧾 <b>{nm}</b> <i>(поїздка чи подія — як назвете)</i>",
        f"💰 Загалом витрачено: <b>{money_uah(total)}</b>",
        "",
        "Баланси (заплатив − має віддати):",
    ]
    for u, net in rows:
        sign = "+" if net > 0 else ""
        lines.append(f"• {user_mention_html(u)}: <b>{sign}{money_uah(net)}</b>")
    await message.reply("\n".join(lines), parse_mode=ParseMode.HTML)


async def send_group_finish(
    message: Message,
    session: AsyncSession,
    *,
    actor_tg_id: int | None = None,
) -> None:
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply("💬 Немає даних про чат.")
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply("🏁 Немає активної поїздки чи події.")
        return
    uid = actor_tg_id if actor_tg_id is not None else message.from_user.id
    creator_tg = trip.created_by.tg_id if trip.created_by else None
    allowed = (creator_tg is not None and creator_tg == uid) or await is_user_group_admin(
        message.bot, message.chat.id, uid
    )
    if not allowed:
        await message.reply(
            "⛔️ Завершити поїздку чи подію можуть лише той, хто її створив, або адміністратори групи."
        )
        return

    nets = await compute_trip_net_by_user(session, trip.id)
    nets = normalize_trip_nets_to_zero_sum(nets)
    transfers = greedy_minimal_transfers(nets)

    trip.is_active = False
    await session.flush()

    nm = html.escape(trip.name or "")
    head = f"🏁 Поїздку / подію «{nm}» завершено!"
    coffee = coffee_footer_html()

    if not transfers:
        body = f"{head}\n✅ Розрахунки збалансовані — переказів не потрібно."
        if coffee:
            body = f"{body}\n\n{coffee}"
        await message.reply(body, parse_mode=ParseMode.HTML)
        return

    user_by_id: dict[int, User] = {}
    for uid in {t[0] for t in transfers} | {t[1] for t in transfers}:
        res = await session.execute(select(User).where(User.id == uid))
        u = res.scalar_one_or_none()
        if u:
            user_by_id[uid] = u

    lines = [head, "", "Мінімальні перекази:", ""]
    for du, cu, amt in transfers:
        du_u = user_by_id.get(du)
        cu_u = user_by_id.get(cu)
        if not du_u or not cu_u:
            continue
        lines.append(
            f"{user_mention_html(du_u)} → {user_mention_html(cu_u)}: <b>{money_uah(amt)}</b>"
        )
    body = "\n".join(lines)
    if coffee:
        body = f"{body}\n\n{coffee}"
    await message.reply(body, parse_mode=ParseMode.HTML)


async def try_create_trip(message: Message, session: AsyncSession, name: str) -> bool:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply("💬 Надішліть будь-яке повідомлення в чат, щоб я запам’ятав учасників, і спробуйте знову.")
        return False
    if await active_trip(session, chat.id):
        await message.reply(
            "⚠️ У цьому чаті вже є активна поїздка чи подія. Завершіть її через меню або /finish_trip."
        )
        return False
    nm = name.strip() or "Поїздка / подія"
    actor = await user_by_tg(session, message.from_user.id)
    if not actor:
        await message.reply("❌ Не вдалося знайти ваш профіль. Напишіть будь-яке повідомлення й повторіть спробу.")
        return False
    trip = Trip(chat_id=chat.id, name=nm, is_active=True, created_by_id=actor.id)
    session.add(trip)
    await session.flush()
    safe = html.escape(nm)
    await message.reply(
        f"✅ Поїздку / подію «{safe}» створено!\nДодавайте витрати через меню або /spent.",
        parse_mode=ParseMode.HTML,
    )
    return True


@router.message(Command("new_trip"))
async def cmd_new_trip(message: Message, command: CommandObject, session: AsyncSession) -> None:
    name = (command.args or "").strip() or "Поїздка / подія"
    await try_create_trip(message, session, name)


@router.message(Command("status"))
async def cmd_status(message: Message, session: AsyncSession) -> None:
    await send_group_status(message, session)


@router.message(Command("finish_trip"))
async def cmd_finish_trip(message: Message, session: AsyncSession) -> None:
    await send_group_finish(message, session, actor_tg_id=None)
