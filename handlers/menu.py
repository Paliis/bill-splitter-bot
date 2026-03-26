from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import MessageEntityType, ParseMode
from aiogram.filters import BaseFilter, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.callback_data import MainMenu, TripCurrency, WizardCancel
from handlers.db_utils import active_trip, chat_by_tg
from handlers.trip_mgmt import send_group_finish, send_group_status, try_create_trip
from keyboards.main_menu import main_menu_kb, trip_currency_kb, wizard_cancel_row
from services.i18n import SUPPORTED_CURRENCIES, Locale, tr
from services.membership import track_user_in_chat
from services.support import help_reply_markup, help_text_html
from services.sync_admins import sync_group_admins
from states import ExpenseSG, TripSG


class _GroupInlineCb(BaseFilter):
    async def __call__(self, callback: CallbackQuery) -> bool:
        return bool(callback.message and callback.message.chat.type in ("group", "supergroup"))


class BotMentionedIdle(BaseFilter):
    async def __call__(self, message: Message, bot: Bot, state: FSMContext) -> bool:
        if message.chat.type not in ("group", "supergroup"):
            return False
        if await state.get_state() is not None:
            return False
        if not message.text:
            return False
        if message.text.strip().startswith("/"):
            return False
        me = await bot.get_me()
        if message.entities:
            for e in message.entities:
                if e.type == MessageEntityType.TEXT_MENTION and e.user and e.user.id == me.id:
                    return True
        if me.username and f"@{me.username}".lower() in message.text.lower():
            return True
        return False


router = Router(name="menu")
router.message.filter(F.chat.type.in_({"group", "supergroup"}))
router.callback_query.filter(_GroupInlineCb())


async def _send_main_menu(message: Message, session: AsyncSession, locale: Locale) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    await message.reply(
        tr(locale, "menu.caption"),
        parse_mode=ParseMode.HTML,
        reply_markup=main_menu_kb(locale),
    )


@router.message(Command("start", "menu"))
async def cmd_start_menu(message: Message, state: FSMContext, session: AsyncSession, locale: Locale) -> None:
    await state.clear()
    await _send_main_menu(message, session, locale)


@router.message(Command("cancel"))
async def cmd_cancel_wizard(message: Message, state: FSMContext, locale: Locale) -> None:
    if await state.get_state() is None:
        await message.reply(tr(locale, "wizard.no_active"), parse_mode=ParseMode.HTML)
        return
    await state.clear()
    await message.reply(tr(locale, "wizard.cancelled_cmd"), parse_mode=ParseMode.HTML)


@router.message(Command("help"))
async def cmd_help(message: Message, state: FSMContext, session: AsyncSession, locale: Locale) -> None:
    await state.clear()
    await sync_group_admins(message.bot, session, message.chat.id)
    await message.reply(
        help_text_html(locale),
        parse_mode=ParseMode.HTML,
        reply_markup=help_reply_markup(locale),
    )


@router.message(Command("here"))
async def cmd_here(message: Message, session: AsyncSession, locale: Locale) -> None:
    u = message.from_user
    if not u or u.is_bot:
        return
    await sync_group_admins(message.bot, session, message.chat.id)
    title = message.chat.title or ""
    await track_user_in_chat(session, u, message.chat.id, title)
    await message.reply(tr(locale, "here.ok"), parse_mode=ParseMode.HTML)


@router.message(BotMentionedIdle(), F.text)
async def on_bot_mentioned(message: Message, session: AsyncSession, locale: Locale) -> None:
    await _send_main_menu(message, session, locale)


@router.callback_query(TripSG.waiting_currency, TripCurrency.filter())
async def cb_trip_currency(
    callback: CallbackQuery,
    state: FSMContext,
    callback_data: TripCurrency,
    locale: Locale,
) -> None:
    if callback_data.code not in SUPPORTED_CURRENCIES:
        await callback.answer()
        return
    await state.update_data(pending_currency=callback_data.code)
    await state.set_state(TripSG.waiting_name)
    await callback.answer()
    kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row(locale)])
    try:
        await callback.message.edit_text(
            tr(locale, "trip.ask_name"),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
    except Exception:
        await callback.message.answer(
            tr(locale, "trip.ask_name"),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )


@router.callback_query(WizardCancel.filter(), TripSG.waiting_currency)
async def cb_wizard_cancel_currency(callback: CallbackQuery, state: FSMContext, locale: Locale) -> None:
    await state.clear()
    await callback.answer(tr(locale, "trip.cancel_short"))
    try:
        await callback.message.edit_text(tr(locale, "trip.cancelled"))
    except Exception:
        await callback.message.answer(tr(locale, "trip.cancelled"))


@router.message(TripSG.waiting_name, F.text, ~F.text.startswith("/"))
async def on_trip_name(message: Message, state: FSMContext, session: AsyncSession, locale: Locale) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.reply(tr(locale, "trip.name_empty"))
        return
    data = await state.get_data()
    cur = str(data.get("pending_currency") or "UAH")
    await try_create_trip(message, session, name, currency=cur, locale=locale)
    await state.clear()


@router.callback_query(WizardCancel.filter(), TripSG.waiting_name)
async def cb_wizard_cancel_trip(callback: CallbackQuery, state: FSMContext, locale: Locale) -> None:
    await state.clear()
    await callback.answer(tr(locale, "trip.cancel_short"))
    try:
        await callback.message.edit_text(tr(locale, "trip.cancelled"))
    except Exception:
        await callback.message.answer(tr(locale, "trip.cancelled"))


@router.callback_query(MainMenu.filter())
async def on_main_menu(
    callback: CallbackQuery,
    state: FSMContext,
    session: AsyncSession,
    callback_data: MainMenu,
    locale: Locale,
) -> None:
    act = callback_data.act
    if act == "mn":
        await callback.answer()
        await state.clear()
        await sync_group_admins(callback.message.bot, session, callback.message.chat.id)
        try:
            await callback.message.edit_text(
                tr(locale, "menu.caption"),
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_kb(locale),
            )
        except Exception:
            await callback.message.answer(
                tr(locale, "menu.caption"),
                parse_mode=ParseMode.HTML,
                reply_markup=main_menu_kb(locale),
            )
        return

    if act == "st":
        await callback.answer()
        await send_group_status(callback.message, session, locale)
        return

    if act == "ft":
        await callback.answer()
        await send_group_finish(callback.message, session, locale, actor_tg_id=callback.from_user.id)
        return

    if act == "nt":
        chat = await chat_by_tg(session, callback.message.chat.id)
        if chat and await active_trip(session, chat.id):
            await callback.answer(tr(locale, "trip.active_exists"), show_alert=True)
            return
        await callback.answer()
        await state.clear()
        if locale == "en":
            await state.set_state(TripSG.waiting_currency)
            await callback.message.answer(
                tr(locale, "trip.pick_currency"),
                parse_mode=ParseMode.HTML,
                reply_markup=trip_currency_kb(locale),
            )
        else:
            await state.set_state(TripSG.waiting_name)
            kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row(locale)])
            await callback.message.answer(
                tr(locale, "trip.ask_name"),
                parse_mode=ParseMode.HTML,
                reply_markup=kb,
            )
        return

    if act == "ex":
        chat = await chat_by_tg(session, callback.message.chat.id)
        if not chat or not await active_trip(session, chat.id):
            await callback.answer(tr(locale, "menu.no_trip_expense"), show_alert=True)
            return
        await callback.answer()
        await state.clear()
        await state.set_state(ExpenseSG.waiting_amount)
        kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row(locale)])
        await callback.message.answer(
            tr(locale, "exp.enter_amount"),
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return

    if act == "cw":
        if await state.get_state() is None:
            await callback.answer(tr(locale, "wizard.no_active"), show_alert=True)
            return
        await callback.answer()
        await state.clear()
        await callback.message.answer(tr(locale, "wizard.cancelled_cmd"), parse_mode=ParseMode.HTML)
        return

    if act == "hp":
        await callback.answer()
        await state.clear()
        await sync_group_admins(callback.message.bot, session, callback.message.chat.id)
        try:
            await callback.message.edit_text(
                help_text_html(locale),
                parse_mode=ParseMode.HTML,
                reply_markup=help_reply_markup(locale),
            )
        except Exception:
            await callback.message.answer(
                help_text_html(locale),
                parse_mode=ParseMode.HTML,
                reply_markup=help_reply_markup(locale),
            )
        return

    await callback.answer()
