from __future__ import annotations

from decimal import Decimal

_STEP = Decimal("0.01")
# Максимальна «копійкова» різниця, яку знімаємо на одного учасника (після округлення нетто).
_MAX_RESIDUAL = Decimal("0.02")


def normalize_trip_nets_to_zero_sum(nets: dict[int, Decimal]) -> dict[int, Decimal]:
    """
    Після quantize по 0.01 сума нетто інколи може відрізнятися від 0 на копійку.
    Знімаємо залишок на найбільшого кредитора або найбільшого дебітора.
    """
    if not nets:
        return {}
    out = {uid: Decimal(str(net)).quantize(_STEP) for uid, net in nets.items()}
    total = sum(out.values(), Decimal("0")).quantize(_STEP)
    if total == 0:
        return out
    if abs(total) > _MAX_RESIDUAL:
        return out
    uid_max = max(out.keys(), key=lambda u: out[u])
    uid_min = min(out.keys(), key=lambda u: out[u])
    if total > 0:
        out[uid_max] = (out[uid_max] - total).quantize(_STEP)
    else:
        out[uid_min] = (out[uid_min] - total).quantize(_STEP)
    return out


def greedy_minimal_transfers(nets: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    debtors: list[list] = []  # [user_id, amount_owed_positive]
    creditors: list[list] = []
    for uid, net in nets.items():
        if net < 0:
            debtors.append([uid, (-net).quantize(Decimal("0.01"))])
        elif net > 0:
            creditors.append([uid, net.quantize(Decimal("0.01"))])

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    out: list[tuple[int, int, Decimal]] = []
    di, ci = 0, 0
    while di < len(debtors) and ci < len(creditors):
        du, d_amt = debtors[di]
        cu, c_amt = creditors[ci]
        pay = min(d_amt, c_amt)
        if pay > 0:
            out.append((du, cu, pay))
        d_amt -= pay
        c_amt -= pay
        debtors[di][1] = d_amt
        creditors[ci][1] = c_amt
        if d_amt == 0:
            di += 1
        if c_amt == 0:
            ci += 1
    return out
