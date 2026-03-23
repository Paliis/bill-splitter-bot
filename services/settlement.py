from __future__ import annotations

from decimal import Decimal


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
