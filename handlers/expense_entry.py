from __future__ import annotations

import html
import logging
import re
from decimal import Decimal

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import BaseFilter, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from formatting import format_trip_money
from handlers.callback_data import (
    ExpCancel,
    ExpConfirm,
    ExpRefreshMembers,
    ExpSplitAll,
    ExpToggle,
    WizardCancel,
)
from handlers.db_utils import active_trip, chat_by_tg
from keyboards.inline_factory import expense_participants_kb, member_labels
from keyboards.main_menu import wizard_cancel_row
from models import ChatMember, Debt, Expense, Trip, User
from services.i18n import Locale, tr
from services.split_amount import split_total_equally
from services.sync_admins import sync_group_admins
from states import ExpenseSG

logger = logging.getLogger(__name__)


class _GroupInlineCallbackFilter(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return bool(callback.message and callback.message.chat.type in ("group", "supergroup"))


router = Router(name="expense_entry")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))
router.callback_query.filter(_GroupInlineCallbackFilter())


def _parse_spent_args(args: str | None) -> tuple[Decimal, str] | None:
    if not args or not str(args).strip():
        return None
    parts = str(args).strip().split(maxsplit=1)
    raw = parts[0].replace(",", ".").replace(" ", "")
    if not re.fullmatch(r"\d+(\.\d+)?", raw):
        return None
    amt = Decimal(raw).quantize(Decimal("0.01"))
    if amt <= 0:
        return None
    desc = parts[1].strip() if len(parts) > 1 else ""
    return amt, desc


def _parse_amount_text(text: str) -> Decimal | None:
    raw = text.strip().replace(",", ".").replace(" ", "")
    if not re.fullmatch(r"\d+(\.\d+)?", raw):
        return None
    amt = Decimal(raw).quantize(Decimal("0.01"))
    if amt <= 0:
        return None
    return amt


async def _members_for_chat(session: AsyncSession, chat_internal_id: int) -> list[User]:
    stmt = select(User).join(ChatMember, ChatMember.user_id == User.id).where(ChatMember.chat_id == chat_internal_id)
    return list((await session.execute(stmt)).scalars())


async def begin_expense_participant_selection(
    message: Message,
    state: FSMContext,
    session: AsyncSession,
    amount: Decimal,
    description: str,
    locale: Locale,
) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply(tr(locale, "exp.no_chat"))
        await state.clear()
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply(tr(locale, "exp.no_trip"))
        await state.clear()
        return
    users = await _members_for_chat(session, chat.id)
    if not users:
        await message.reply(tr(locale, "exp.no_members_db"))
        await state.clear()
        return

    cc = trip.currency or "UAH"
    await state.set_state(ExpenseSG.choosing_participants)
    await state.update_data(
        trip_id=trip.id,
        amount=str(amount),
        description=description,
        selected=[],
        initiator_tg_id=message.from_user.id,
        locale=locale,
    )
    kb = expense_participants_kb(member_labels(users, locale), set(), locale)
    amt_s = format_trip_money(amount, cc, locale)
    title = f"🧾 Витрата: <b>{amt_s}</b>"
    if description:
        title += f"\n📝 {description}"
    title += tr(locale, "exp.split_hint")
    await message.reply(title, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(
    WizardCancel.filter(),
    StateFilter(ExpenseSG.waiting_amount, ExpenseSG.waiting_description),
)
async def cb_wizard_cancel_expense(callback: CallbackQuery, state: FSMContext, locale: Locale) -> None:
    await state.clear()
    await callback.answer(tr(locale, "trip.cancel_short"))
    try:
        await callback.message.edit_text(tr(locale, "exp.wizard_cancelled"))
    except Exception:
        await callback.message.answer(tr(locale, "exp.wizard_cancelled"))


@router.message(Command("spent"))
async def cmd_spent(
    message: Message,
    command: CommandObject,
    state: FSMContext,
    session: AsyncSession,
    locale: Locale,
) -> None:
    parsed = _parse_spent_args(command.args)
    if parsed:
        amount, description = parsed
        await begin_expense_participant_selection(message, state, session, amount, description, locale)
        return

    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat or not await active_trip(session, chat.id):
        await message.reply(tr(locale, "exp.no_active_cmd"), parse_mode=ParseMode.HTML)
        return
    await state.clear()
    await state.set_state(ExpenseSG.waiting_amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row(locale)])
    await message.reply(
        tr(locale, "exp.enter_amount_hint"),
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


@router.message(ExpenseSG.waiting_amount, F.text, ~F.text.startswith("/"))
async def on_expense_amount(message: Message, state: FSMContext, session: AsyncSession, locale: Locale) -> None:
    amt = _parse_amount_text(message.text or "")
    if amt is None:
        await message.reply(tr(locale, "exp.bad_amount"), parse_mode=ParseMode.HTML)
        return
    await state.update_data(pending_amount=str(amt))
    await state.set_state(ExpenseSG.waiting_description)
    kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row(locale)])
    await message.reply(
        tr(locale, "exp.ask_desc"),
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


@router.message(ExpenseSG.waiting_description, F.text, ~F.text.startswith("/"))
async def on_expense_description(message: Message, state: FSMContext, session: AsyncSession, locale: Locale) -> None:
    raw = (message.text or "").strip()
    desc = "" if raw in ("-", "—", "пропустити", "ні", "немає", "skip", "none") else raw
    data = await state.get_data()
    amount = Decimal(str(data.get("pending_amount", "0")))
    await begin_expense_participant_selection(message, state, session, amount, desc, locale)


def _locale_from_state(data: dict) -> Locale:
    loc = data.get("locale")
    return loc if loc in ("uk", "en") else "uk"


async def _reload_members_kb(
    session: AsyncSession, chat_internal_id: int, selected: set[int], locale: Locale
):
    users = await _members_for_chat(session, chat_internal_id)
    return expense_participants_kb(member_labels(users, locale), selected, locale)


@router.callback_query(ExpenseSG.choosing_participants, ExpSplitAll.filter())
async def cb_split_all(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    loc = _locale_from_state(data)
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer(tr(loc, "exp.not_for_you"), show_alert=True)
        return
    chat = await chat_by_tg(session, callback.message.chat.id)
    if not chat:
        await callback.answer(tr(loc, "exp.chat_not_found"), show_alert=True)
        return
    users = await _members_for_chat(session, chat.id)
    selected = {u.id for u in users}
    await state.update_data(selected=list(selected))
    kb = await _reload_members_kb(session, chat.id, selected, loc)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(ExpenseSG.choosing_participants, ExpRefreshMembers.filter())
async def cb_refresh_members(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    loc = _locale_from_state(data)
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer(tr(loc, "exp.not_for_you"), show_alert=True)
        return
    await sync_group_admins(callback.bot, session, callback.message.chat.id)
    chat = await chat_by_tg(session, callback.message.chat.id)
    if not chat:
        await callback.answer(tr(loc, "exp.chat_not_found"), show_alert=True)
        return
    users = await _members_for_chat(session, chat.id)
    valid_ids = {u.id for u in users}
    cur = {int(x) for x in (data.get("selected") or [])}
    cur &= valid_ids
    await state.update_data(selected=list(cur))
    kb = await _reload_members_kb(session, chat.id, cur, loc)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer(tr(loc, "exp.list_refreshed"))


@router.callback_query(ExpenseSG.choosing_participants, ExpToggle.filter())
async def cb_toggle(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    callback_data: ExpToggle,
) -> None:
    data = await state.get_data()
    loc = _locale_from_state(data)
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer(tr(loc, "exp.not_for_you"), show_alert=True)
        return
    chat = await chat_by_tg(session, callback.message.chat.id)
    if not chat:
        await callback.answer(tr(loc, "exp.chat_not_found"), show_alert=True)
        return
    uid = callback_data.user_id
    cur = set(int(x) for x in (data.get("selected") or []))
    if uid in cur:
        cur.remove(uid)
    else:
        cur.add(uid)
    await state.update_data(selected=list(cur))
    kb = await _reload_members_kb(session, chat.id, cur, loc)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(ExpenseSG.choosing_participants, ExpConfirm.filter())
async def cb_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    loc = _locale_from_state(data)
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer(tr(loc, "exp.not_for_you"), show_alert=True)
        return
    selected = sorted(int(x) for x in (data.get("selected") or []))
    if not selected:
        await callback.answer(tr(loc, "exp.pick_one"), show_alert=True)
        return
    amount = Decimal(str(data["amount"]))
    description = str(data.get("description") or "")
    trip_id = int(data["trip_id"])

    payer_res = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
    payer = payer_res.scalar_one_or_none()
    if not payer:
        await callback.answer(tr(loc, "exp.user_not_found"), show_alert=True)
        return

    await callback.answer()

    trip_row = await session.get(Trip, trip_id)
    cc = (trip_row.currency if trip_row else None) or "UAH"

    shares = split_total_equally(amount, len(selected))
    uid_to_share = {uid: sh for uid, sh in zip(selected, shares)}

    exp = Expense(trip_id=trip_id, payer_id=payer.id, amount=amount, description=description)
    session.add(exp)
    await session.flush()

    for uid in selected:
        session.add(Debt(expense_id=exp.id, debtor_id=uid, amount=uid_to_share[uid]))

    payer_label = html.escape(payer.full_name or tr(loc, "user.default"), quote=False)
    desc_html = html.escape(description, quote=False) if description else ""
    amt_disp = format_trip_money(amount, cc, loc)
    lines = [
        tr(loc, "exp.saved", amount=amt_disp),
        *([f"📝 {desc_html}"] if desc_html else []),
        tr(loc, "exp.payer", name=payer_label),
    ]
    body = "\n".join(lines)

    try:
        await callback.message.edit_text(body, parse_mode=ParseMode.HTML)
    except Exception:
        logger.exception("edit_text after expense save failed")
        await callback.message.answer(body, parse_mode=ParseMode.HTML)

    await state.clear()


@router.callback_query(ExpenseSG.choosing_participants, ExpCancel.filter())
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    loc = _locale_from_state(data)
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer(tr(loc, "exp.not_for_you"), show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text(tr(loc, "exp.cancelled_flow"))
    await callback.answer()
