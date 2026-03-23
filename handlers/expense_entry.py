from __future__ import annotations

import re
from decimal import Decimal

from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import BaseFilter, Command, CommandObject, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from formatting import money_uah
from handlers.callback_data import ExpCancel, ExpConfirm, ExpSplitAll, ExpToggle, WizardCancel
from handlers.db_utils import active_trip, chat_by_tg
from keyboards.inline_factory import expense_participants_kb, member_labels
from keyboards.main_menu import wizard_cancel_row
from models import ChatMember, Debt, Expense, User
from services.split_amount import split_total_equally
from services.sync_admins import sync_group_admins
from states import ExpenseSG


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
) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat:
        await message.reply("💬 Спочатку напишіть повідомлення в чаті, щоб я бачив учасників.")
        await state.clear()
        return
    trip = await active_trip(session, chat.id)
    if not trip:
        await message.reply("🧾 Немає активної поїздки чи події. Створіть її через меню.")
        await state.clear()
        return
    users = await _members_for_chat(session, chat.id)
    if not users:
        await message.reply("👥 У чаті ще немає учасників у моїй базі. Напишіть повідомлення в групі.")
        await state.clear()
        return

    await state.set_state(ExpenseSG.choosing_participants)
    await state.update_data(
        trip_id=trip.id,
        amount=str(amount),
        description=description,
        selected=[],
        initiator_tg_id=message.from_user.id,
    )
    kb = expense_participants_kb(member_labels(users), set())
    title = f"🧾 Витрата: <b>{money_uah(amount)}</b>"
    if description:
        title += f"\n📝 {description}"
    title += (
        "\n\nОберіть, між ким ділити суму, або «Розділити на всіх»."
        "\n\n<i>Немає когось з учасників? Нехай напише будь-яке повідомлення в чат "
        "(або додайте в групу знову) — тоді з’явиться в списку.</i>"
    )
    await message.reply(title, parse_mode=ParseMode.HTML, reply_markup=kb)


@router.callback_query(
    WizardCancel.filter(),
    StateFilter(ExpenseSG.waiting_amount, ExpenseSG.waiting_description),
)
async def cb_wizard_cancel_expense(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Скасовано")
    try:
        await callback.message.edit_text("❌ Скасовано.")
    except Exception:
        await callback.message.answer("❌ Скасовано.")


@router.message(Command("spent"))
async def cmd_spent(message: Message, command: CommandObject, state: FSMContext, session: AsyncSession) -> None:
    parsed = _parse_spent_args(command.args)
    if parsed:
        amount, description = parsed
        await begin_expense_participant_selection(message, state, session, amount, description)
        return

    # Меню Telegram надсилає лише /spent@bot без аргументів — той самий крок, що кнопка «Додати витрату».
    await sync_group_admins(message.bot, session, message.chat.id)
    chat = await chat_by_tg(session, message.chat.id)
    if not chat or not await active_trip(session, chat.id):
        await message.reply(
            "🧾 Немає активної поїздки чи події. Створіть її через меню або <code>/new_trip</code>.",
            parse_mode=ParseMode.HTML,
        )
        return
    await state.clear()
    await state.set_state(ExpenseSG.waiting_amount)
    kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row()])
    await message.reply(
        "💸 Введіть <b>суму</b> витрати (наприклад <code>100</code> або <code>50.25</code>).\n"
        "Або одним повідомленням: <code>/spent 250.50 Кава</code>.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


@router.message(ExpenseSG.waiting_amount, F.text, ~F.text.startswith("/"))
async def on_expense_amount(message: Message, state: FSMContext, session: AsyncSession) -> None:
    amt = _parse_amount_text(message.text or "")
    if amt is None:
        await message.reply("❌ Введіть суму числом, наприклад <code>100</code> або <code>50.25</code>", parse_mode=ParseMode.HTML)
        return
    await state.update_data(pending_amount=str(amt))
    await state.set_state(ExpenseSG.waiting_description)
    kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row()])
    await message.reply(
        "📝 Напишіть короткий опис витрати одним повідомленням.\n"
        "Або надішліть <code>-</code>, щоб залишити без опису.",
        parse_mode=ParseMode.HTML,
        reply_markup=kb,
    )


@router.message(ExpenseSG.waiting_description, F.text, ~F.text.startswith("/"))
async def on_expense_description(message: Message, state: FSMContext, session: AsyncSession) -> None:
    raw = (message.text or "").strip()
    desc = "" if raw in ("-", "—", "пропустити", "ні", "немає") else raw
    data = await state.get_data()
    amount = Decimal(str(data.get("pending_amount", "0")))
    await begin_expense_participant_selection(message, state, session, amount, desc)


async def _reload_members_kb(session: AsyncSession, chat_internal_id: int, selected: set[int]):
    users = await _members_for_chat(session, chat_internal_id)
    return expense_participants_kb(member_labels(users), selected)


@router.callback_query(ExpenseSG.choosing_participants, ExpSplitAll.filter())
async def cb_split_all(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer("⛔️ Це меню не для вас.", show_alert=True)
        return
    chat = await chat_by_tg(session, callback.message.chat.id)
    if not chat:
        await callback.answer("Чат не знайдено.", show_alert=True)
        return
    users = await _members_for_chat(session, chat.id)
    selected = {u.id for u in users}
    await state.update_data(selected=list(selected))
    kb = await _reload_members_kb(session, chat.id, selected)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(ExpenseSG.choosing_participants, ExpToggle.filter())
async def cb_toggle(callback: CallbackQuery, state: FSMContext, session: AsyncSession, callback_data: ExpToggle) -> None:
    data = await state.get_data()
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer("⛔️ Це меню не для вас.", show_alert=True)
        return
    chat = await chat_by_tg(session, callback.message.chat.id)
    if not chat:
        await callback.answer("Чат не знайдено.", show_alert=True)
        return
    uid = callback_data.user_id
    cur = set(int(x) for x in (data.get("selected") or []))
    if uid in cur:
        cur.remove(uid)
    else:
        cur.add(uid)
    await state.update_data(selected=list(cur))
    kb = await _reload_members_kb(session, chat.id, cur)
    await callback.message.edit_reply_markup(reply_markup=kb)
    await callback.answer()


@router.callback_query(ExpenseSG.choosing_participants, ExpConfirm.filter())
async def cb_confirm(callback: CallbackQuery, state: FSMContext, session: AsyncSession) -> None:
    data = await state.get_data()
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer("⛔️ Це меню не для вас.", show_alert=True)
        return
    selected = sorted(int(x) for x in (data.get("selected") or []))
    if not selected:
        await callback.answer("Оберіть хоча б одного учасника.", show_alert=True)
        return
    amount = Decimal(str(data["amount"]))
    description = str(data.get("description") or "")
    trip_id = int(data["trip_id"])

    payer_res = await session.execute(select(User).where(User.tg_id == callback.from_user.id))
    payer = payer_res.scalar_one_or_none()
    if not payer:
        await callback.answer("Користувача не знайдено.", show_alert=True)
        return

    shares = split_total_equally(amount, len(selected))
    uid_to_share = {uid: sh for uid, sh in zip(selected, shares)}

    exp = Expense(trip_id=trip_id, payer_id=payer.id, amount=amount, description=description)
    session.add(exp)
    await session.flush()

    # Частка платника теж у Debt, інакше net платника = уся сума витрати.
    for uid in selected:
        session.add(Debt(expense_id=exp.id, debtor_id=uid, amount=uid_to_share[uid]))

    await state.clear()
    await callback.message.edit_text(
        f"✅ Збережено витрату {money_uah(amount)}"
        + (f"\n📝 {description}" if description else "")
        + f"\n👤 Платник: {payer.full_name}",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer("Готово!")


@router.callback_query(ExpenseSG.choosing_participants, ExpCancel.filter())
async def cb_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    data = await state.get_data()
    if callback.from_user.id != data.get("initiator_tg_id"):
        await callback.answer("⛔️ Це меню не для вас.", show_alert=True)
        return
    await state.clear()
    await callback.message.edit_text("❌ Введення витрати скасовано.")
    await callback.answer()
