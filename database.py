import logging
import os

from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from models import Base
from services.balances import repair_legacy_payer_debts

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./bot.db")

logger = logging.getLogger(__name__)


def _warn_if_data_may_reset_on_deploy() -> None:
    """SQLite у файлі на диску воркера (Render тощо) зазвичай зникає після деплою — потрібен зовнішній PostgreSQL."""
    if "sqlite" not in DATABASE_URL.lower():
        return
    logger.warning(
        "DATABASE_URL вказує на SQLite. У продакшені на хостингах без постійного диска файл БД "
        "часто створюється наново після кожного деплою — зникають учасники, чати й витрати. "
        "Щоб дані зберігались між білдами, підключіть PostgreSQL (Neon, Supabase, Render Postgres) "
        "і задайте DATABASE_URL з префіксом postgresql+asyncpg://"
    )

engine = create_async_engine(DATABASE_URL, echo=False)
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def init_db() -> None:
    _warn_if_data_may_reset_on_deploy()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with async_session_maker() as session:
        fixed = await repair_legacy_payer_debts(session)
        await session.commit()
    if fixed:
        logger.info("Виправлено записи боргів (стара логіка): %s витрат", fixed)
