from __future__ import annotations

from decimal import Decimal


def split_total_equally(total: Decimal, parts: int) -> list[Decimal]:
    if parts <= 0:
        raise ValueError("parts must be positive")
    total = total.quantize(Decimal("0.01"))
    cents = int(total * 100)
    base, rem = divmod(cents, parts)
    out: list[Decimal] = []
    for i in range(parts):
        c = base + (1 if i < rem else 0)
        out.append(Decimal(c) / Decimal(100))
    return out
