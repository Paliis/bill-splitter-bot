from __future__ import annotations

from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from models import ChatMember, Debt, Expense, Trip, User


async def compute_trip_net_by_user(session: AsyncSession, trip_id: int) -> dict[int, Decimal]:
    paid_rows = await session.execute(
        select(Expense.payer_id, func.coalesce(func.sum(Expense.amount), 0)).where(Expense.trip_id == trip_id).group_by(Expense.payer_id)
    )
    owed_rows = await session.execute(
        select(Debt.debtor_id, func.coalesce(func.sum(Debt.amount), 0))
        .join(Expense, Expense.id == Debt.expense_id)
        .where(Expense.trip_id == trip_id)
        .group_by(Debt.debtor_id)
    )
    paid: dict[int, Decimal] = {int(r[0]): Decimal(r[1]) for r in paid_rows.all()}
    owed: dict[int, Decimal] = {int(r[0]): Decimal(r[1]) for r in owed_rows.all()}
    uids = set(paid) | set(owed)
    return {uid: paid.get(uid, Decimal("0")) - owed.get(uid, Decimal("0")) for uid in uids}


async def trip_total_spent(session: AsyncSession, trip_id: int) -> Decimal:
    res = await session.execute(select(func.coalesce(func.sum(Expense.amount), 0)).where(Expense.trip_id == trip_id))
    return Decimal(res.scalar_one())


async def repair_legacy_payer_debts(session: AsyncSession) -> int:
    """Дописати Debt платнику, якщо сума боргів < суми витрати (дані до виправлення логіки)."""
    from sqlalchemy.orm import selectinload

    stmt = select(Expense).options(selectinload(Expense.debts))
    expenses = (await session.execute(stmt)).scalars().all()
    n = 0
    for exp in expenses:
        total = sum((d.amount for d in exp.debts), Decimal("0"))
        gap = (exp.amount - total).quantize(Decimal("0.01"))
        if gap <= Decimal("0"):
            continue
        session.add(Debt(expense_id=exp.id, debtor_id=exp.payer_id, amount=gap))
        n += 1
    return n


async def list_chat_member_balances(session: AsyncSession, trip: Trip) -> list[tuple[User, Decimal]]:
    stmt = (
        select(User)
        .join(ChatMember, ChatMember.user_id == User.id)
        .where(ChatMember.chat_id == trip.chat_id)
        .order_by(User.full_name)
    )
    users = list((await session.execute(stmt)).scalars())
    nets = await compute_trip_net_by_user(session, trip.id)
    return [(u, nets.get(u.id, Decimal("0"))) for u in users]
