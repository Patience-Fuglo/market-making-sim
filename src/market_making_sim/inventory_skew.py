"""Dynamic inventory skew: simulating a market maker's inventory as it
actually evolves over a real trading session, not a single frozen
snapshot.

Ties together two pieces already built: the Avellaneda-Stoikov quote
(reservation price + spread, which depends on CURRENT inventory) and
real price action (whether the quote actually gets touched). At each
real bar, this recomputes the quote from the market maker's current
inventory, checks whether the real bar's range crossed the bid or ask,
updates inventory if so, and moves to the next real bar with the
UPDATED inventory feeding the next quote -- the real feedback loop.

Fill detection uses real OHLC bars directly: if a real bar's low reached
the quoted bid, the bid is treated as filled (inventory grows); if the
real high reached the quoted ask, the ask is treated as filled
(inventory shrinks). Both can happen in the same volatile real bar.

``time_remaining`` for each bar's quote shrinks from ~1.0 toward 0 across
the real session, matching the underlying Avellaneda-Stoikov model's own
assumption that risk-driven skew fades as the session's end approaches.
"""

from __future__ import annotations

import pandas as pd
from avellaneda_stoikov import quote


def simulate_inventory_trajectory(
    price_bars: pd.DataFrame,
    initial_inventory: float,
    risk_aversion: float,
    volatility: float,
    order_arrival_sensitivity: float,
    fill_size: float,
) -> pd.DataFrame:
    """Simulate inventory evolving bar by bar over a real trading session.

    ``price_bars`` must have real ``high``, ``low``, ``close`` columns.
    Returns one row per bar: ``inventory`` (after any fills that bar),
    ``bid``, ``ask``, ``reservation_price``, and whether each side filled.
    """
    if len(price_bars) == 0:
        raise ValueError("price_bars must not be empty")
    if fill_size <= 0:
        raise ValueError("fill_size must be positive")

    n = len(price_bars)
    inventory = initial_inventory
    rows = []

    for i, (idx, bar) in enumerate(price_bars.iterrows()):
        time_remaining = 1.0 - i / n
        mid = float(bar["close"])
        q = quote(
            mid_price=mid, inventory=inventory, risk_aversion=risk_aversion,
            volatility=volatility, time_remaining=time_remaining,
            order_arrival_sensitivity=order_arrival_sensitivity,
        )
        bid_filled = float(bar["low"]) <= q.bid
        ask_filled = float(bar["high"]) >= q.ask
        if bid_filled:
            inventory += fill_size
        if ask_filled:
            inventory -= fill_size

        rows.append({
            "time": idx,
            "mid_price": mid,
            "reservation_price": q.reservation_price,
            "bid": q.bid,
            "ask": q.ask,
            "bid_filled": bid_filled,
            "ask_filled": ask_filled,
            "inventory": inventory,
        })

    return pd.DataFrame(rows)
