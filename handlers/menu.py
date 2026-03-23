from __future__ import annotations

from aiogram import Bot, F, Router
from aiogram.enums import MessageEntityType, ParseMode
from aiogram.filters import BaseFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from handlers.callback_data import MainMenu, WizardCancel
from handlers.db_utils import active_trip, chat_by_tg
from handlers.trip_mgmt import send_group_finish, send_group_status, try_create_trip
from keyboards.main_menu import main_menu_kb, wizard_cancel_row
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


def _menu_caption() -> str:
    return (
        "📋 <b>Bill Splitter</b>\n"
        "Оберіть дію нижче, згадайте мене через @ або <code>/menu</code>.\n"
        "Адмінів підтягую сам; інші — коли напишуть у чат (якщо бот бачить повідомлення) або <code>/here</code>.\n"
        "«Поїздка» і «подія» — це одне й те саме тут: спільний період витрат.\n"
        "Текстом: <code>/new_trip</code>, <code>/spent</code>, <code>/status</code>, <code>/finish_trip</code>, <code>/help</code>, <code>/here</code>"
    )


async def _send_main_menu(message: Message, session: AsyncSession) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    await message.reply(_menu_caption(), parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())


@router.message(Command("start", "menu"))
async def cmd_start_menu(message: Message, session: AsyncSession) -> None:
    await _send_main_menu(message, session)


@router.message(Command("help"))
async def cmd_help(message: Message, session: AsyncSession) -> None:
    await sync_group_admins(message.bot, session, message.chat.id)
    await message.reply(help_text_html(), parse_mode=ParseMode.HTML, reply_markup=help_reply_markup())


@router.message(Command("here"))
async def cmd_here(message: Message, session: AsyncSession) -> None:
    """Додає відправника в ChatMember; працює навіть коли в групі ввімкнено Privacy (команди завжди доходять)."""
    u = message.from_user
    if not u or u.is_bot:
        return
    await sync_group_admins(message.bot, session, message.chat.id)
    title = message.chat.title or ""
    await track_user_in_chat(session, u, message.chat.id, title)
    await message.reply(
        "✅ Вас додано до списку учасників для поділу витрат у цій групі.\n"
        "Якщо когось немає в списку при витраті — нехай теж надішле <code>/here</code> сюди.",
        parse_mode=ParseMode.HTML,
    )


@router.message(BotMentionedIdle(), F.text)
async def on_bot_mentioned(message: Message, session: AsyncSession) -> None:
    await _send_main_menu(message, session)


@router.message(TripSG.waiting_name, F.text, ~F.text.startswith("/"))
async def on_trip_name(message: Message, state: FSMContext, session: AsyncSession) -> None:
    name = (message.text or "").strip()
    if not name:
        await message.reply("❌ Назва не може бути порожньою.")
        return
    await try_create_trip(message, session, name)
    await state.clear()


@router.callback_query(WizardCancel.filter(), TripSG.waiting_name)
async def cb_wizard_cancel_trip(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Скасовано")
    try:
        await callback.message.edit_text("❌ Створення поїздки / події скасовано.")
    except Exception:
        await callback.message.answer("❌ Створення поїздки / події скасовано.")


@router.callback_query(MainMenu.filter())
async def on_main_menu(callback: CallbackQuery, state: FSMContext, session: AsyncSession, callback_data: MainMenu) -> None:
    act = callback_data.act
    if act == "mn":
        await callback.answer()
        await sync_group_admins(callback.message.bot, session, callback.message.chat.id)
        try:
            await callback.message.edit_text(_menu_caption(), parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
        except Exception:
            await callback.message.answer(_menu_caption(), parse_mode=ParseMode.HTML, reply_markup=main_menu_kb())
        return

    if act == "st":
        await callback.answer()
        await send_group_status(callback.message, session)
        return

    if act == "ft":
        await callback.answer()
        await send_group_finish(callback.message, session, actor_tg_id=callback.from_user.id)
        return

    if act == "nt":
        chat = await chat_by_tg(session, callback.message.chat.id)
        if chat and await active_trip(session, chat.id):
            await callback.answer("Уже є активна поїздка чи подія. Завершіть її спочатку.", show_alert=True)
            return
        await callback.answer()
        await state.clear()
        await state.set_state(TripSG.waiting_name)
        kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row()])
        await callback.message.answer(
            "🆕 Напишіть <b>назву поїздки або події</b> одним повідомленням у чат.",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return

    if act == "ex":
        chat = await chat_by_tg(session, callback.message.chat.id)
        if not chat or not await active_trip(session, chat.id):
            await callback.answer(
                "Немає активної поїздки чи події. Спочатку створіть її через «Нова поїздка / подія».",
                show_alert=True,
            )
            return
        await callback.answer()
        await state.clear()
        await state.set_state(ExpenseSG.waiting_amount)
        kb = InlineKeyboardMarkup(inline_keyboard=[wizard_cancel_row()])
        await callback.message.answer(
            "💸 Введіть <b>суму</b> витрати (наприклад <code>100</code> або <code>50.25</code>).",
            parse_mode=ParseMode.HTML,
            reply_markup=kb,
        )
        return

    if act == "hp":
        await callback.answer()
        await sync_group_admins(callback.message.bot, session, callback.message.chat.id)
        try:
            await callback.message.edit_text(help_text_html(), parse_mode=ParseMode.HTML, reply_markup=help_reply_markup())
        except Exception:
            await callback.message.answer(help_text_html(), parse_mode=ParseMode.HTML, reply_markup=help_reply_markup())
        return

    await callback.answer()
