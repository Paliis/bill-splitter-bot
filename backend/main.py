"""
Bill Splitter HTTP API — окремий процес від Telegram-бота (Render: Web Service).
Запуск з кореня репо: PYTHONPATH=. uvicorn backend.main:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Annotated, Any, Optional

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from database import async_session_maker, init_db
from models import Trip

logger = logging.getLogger(__name__)

API_SECRET = os.getenv("API_SECRET", "").strip()


def _trip_status(is_active: bool) -> str:
    return "active" if is_active else "settled"


def _trip_to_json(t: Trip) -> dict[str, Any]:
    created: datetime = t.created_at
    if created.tzinfo is None:
        created_iso = created.isoformat() + "Z"
    else:
        created_iso = created.isoformat()
    return {
        "id": t.id,
        "partyId": t.chat_id,
        "name": t.name,
        "currency": t.currency or "UAH",
        "status": _trip_status(t.is_active),
        "createdAt": created_iso,
        "createdByUserId": t.created_by_id,
    }


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session


def require_api_secret(x_api_secret: Annotated[Optional[str], Header(alias="X-Api-Secret")] = None) -> None:
    """Якщо задано API_SECRET у .env — усі запити до /v1/* мають містити збіг у заголовку."""
    if not API_SECRET:
        return
    if not x_api_secret or x_api_secret != API_SECRET:
        raise HTTPException(status_code=401, detail="Invalid or missing X-Api-Secret")


@asynccontextmanager
async def lifespan(_app: FastAPI):
    await init_db()
    if not API_SECRET:
        logger.warning(
            "API_SECRET не задано — ендпоінти /v1/* доступні без ключа (лише для локальної розробки). "
            "У проді задайте API_SECRET і передавайте X-Api-Secret."
        )
    yield


app = FastAPI(
    title="Bill Splitter API",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/v1/trips/{trip_id}", dependencies=[Depends(require_api_secret)])
async def get_trip(
    trip_id: int,
    session: Annotated[AsyncSession, Depends(get_session)],
):
    trip = (await session.execute(select(Trip).where(Trip.id == trip_id))).scalar_one_or_none()
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return JSONResponse(content=_trip_to_json(trip))
