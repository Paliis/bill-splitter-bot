"""
Запуск: скопіюйте .env.example у .env і задайте BOT_TOKEN (і за потреби DATABASE_URL).
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import BotCommand
from dotenv import load_dotenv

from database import init_db
from handlers import expense_entry, menu, onboarding, trip_mgmt
from middlewares import DbSessionMiddleware, LocaleMiddleware, TrackGroupMembersMiddleware

load_dotenv()

logging.basicConfig(level=logging.INFO, stream=sys.stdout)


async def _main() -> None:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("Не задано BOT_TOKEN у .env")

    await init_db()

    bot = Bot(token=token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.update.middleware(TrackGroupMembersMiddleware())
    dp.update.middleware(LocaleMiddleware())
    dp.update.middleware(DbSessionMiddleware())

    dp.include_router(onboarding.router)
    dp.include_router(trip_mgmt.router)
    dp.include_router(menu.router)
    dp.include_router(expense_entry.router)

    await bot.set_my_commands(
        [
            BotCommand(command="start", description="Меню з кнопками (у групі)"),
            BotCommand(command="menu", description="Відкрити меню кнопок"),
            BotCommand(command="new_trip", description="Нова поїздка або подія"),
            BotCommand(command="status", description="Баланси та сума витрат"),
            BotCommand(command="spent", description="Додати витрату (або сума в одному рядку)"),
            BotCommand(command="finish_trip", description="Завершити поїздку/подію та розрахунок"),
            BotCommand(command="help", description="Допомога та як користуватись ботом"),
            BotCommand(command="here", description="Додати себе в список учасників групи"),
        ]
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(_main())
