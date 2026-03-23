import logging
import os
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

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


def _asyncpg_url_and_connect_args(url: str) -> tuple[str, dict]:
    """Neon/libpq дають ?sslmode=require — asyncpg це не приймає; прибираємо й вмикаємо ssl=True."""
    if "+asyncpg" not in url.lower():
        return url, {}
    parsed = urlparse(url)
    pairs = parse_qsl(parsed.query, keep_blank_values=True)
    had_sslmode = False
    kept: list[tuple[str, str]] = []
    for k, v in pairs:
        lk = k.lower()
        if lk == "sslmode":
            had_sslmode = True
            continue
        if lk == "channel_binding":
            continue
        kept.append((k, v))
    new_query = urlencode(kept)
    new_url = urlunparse(parsed._replace(query=new_query))
    extra: dict = {}
    if had_sslmode:
        extra["connect_args"] = {"ssl": True}
    return new_url, extra


_engine_url, _engine_kw = _asyncpg_url_and_connect_args(DATABASE_URL)
engine = create_async_engine(_engine_url, echo=False, **_engine_kw)
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
