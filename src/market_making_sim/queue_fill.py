"""Queue-aware fill modeling: given a real trace of trading volume and a
fixed queue position, does a resting order actually get filled, and when?

Real tick-by-tick order flow isn't freely available (yfinance provides
real OHLCV bars, not Level 2/tick data), so this reuses real per-period
*volume* as the trading-activity input instead -- honestly scoped to
that real, coarser granularity rather than faking tick-level precision.

Not every real trade happens at any one specific price level -- most
volume clusters near the best bid/ask, spread across nearby levels.
``participation_rate`` is the assumed fraction of each real period's
volume that trades through this specific quoted level -- an illustrative
design parameter, the same convention as ``gamma``/``k`` in
avellaneda-stoikov-calculator, not something fetched from data.
"""

from __future__ import annotations

from typing import Sequence


def simulate_queue_fill(
    queue_ahead: float,
    own_order_size: float,
    volume_trace: Sequence[float],
    participation_rate: float = 0.1,
) -> dict:
    """Walk a real volume trace period by period: first consume
    ``queue_ahead`` (the real size resting in front of this order), then
    fill ``own_order_size`` once the queue ahead is exhausted.

    Returns ``{"filled": bool, "fill_period": int | None,
    "periods_to_fill": int | None}`` -- ``fill_period`` is the 0-indexed
    period in which the order size hits zero remaining; ``None`` if the
    order never fills within the given real trace.
    """
    if queue_ahead < 0:
        raise ValueError("queue_ahead cannot be negative")
    if own_order_size <= 0:
        raise ValueError("own_order_size must be positive")
    if not 0 < participation_rate <= 1:
        raise ValueError("participation_rate must be in (0, 1]")

    remaining_queue = queue_ahead
    remaining_own = own_order_size

    for i, volume in enumerate(volume_trace):
        available = volume * participation_rate
        if remaining_queue > 0:
            consumed = min(remaining_queue, available)
            remaining_queue -= consumed
            available -= consumed
        if remaining_queue <= 0 and available > 0:
            fill_amt = min(remaining_own, available)
            remaining_own -= fill_amt
            if remaining_own <= 0:
                return {"filled": True, "fill_period": i, "periods_to_fill": i + 1}

    return {"filled": False, "fill_period": None, "periods_to_fill": None}
