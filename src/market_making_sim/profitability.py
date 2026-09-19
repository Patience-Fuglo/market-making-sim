"""Maker-vs-taker profitability: the real P&L a market maker actually
earns from posting resting quotes and capturing the spread, versus what
a taker crossing the spread on the same trades would have paid.

A maker's profit comes from the spread itself, captured repeatedly:
buy at the bid, sell at the ask, pocket the gap, many times over a real
session. The real risk that eats into it is being left holding unsold
inventory when the session ends -- marked to the real final price,
which may have moved against that position.
"""

from __future__ import annotations

import pandas as pd


def compute_maker_pnl(trajectory: pd.DataFrame, fill_size: float) -> dict:
    """Real maker P&L from a completed ``simulate_inventory_trajectory``
    run: realized spread capture on every real fill, plus mark-to-market
    on whatever real inventory is left at the end of the session.

    ``trajectory`` must have the columns ``simulate_inventory_trajectory``
    produces: ``bid``, ``ask``, ``bid_filled``, ``ask_filled``,
    ``inventory``, ``mid_price``. ``fill_size`` is the same real per-fill
    trade size passed to ``simulate_inventory_trajectory`` -- each fill's
    cash flow is price times this size, not price alone.
    """
    if len(trajectory) == 0:
        raise ValueError("trajectory must not be empty")
    if fill_size <= 0:
        raise ValueError("fill_size must be positive")

    bid_fills = trajectory[trajectory["bid_filled"]]
    ask_fills = trajectory[trajectory["ask_filled"]]

    # each real fill's cash flow: buying fill_size at the bid is a cash
    # outflow, selling fill_size at the ask is a cash inflow -- realized_cash
    # nets them across every real fill in the session
    cash_out_from_buys = float(bid_fills["bid"].sum()) * fill_size
    cash_in_from_sells = float(ask_fills["ask"].sum()) * fill_size
    realized_cash = cash_in_from_sells - cash_out_from_buys

    final_inventory = float(trajectory["inventory"].iloc[-1])
    final_mid_price = float(trajectory["mid_price"].iloc[-1])
    mark_to_market = final_inventory * final_mid_price

    total_pnl = realized_cash + mark_to_market

    return {
        "n_bid_fills": len(bid_fills),
        "n_ask_fills": len(ask_fills),
        "realized_cash": realized_cash,
        "final_inventory": final_inventory,
        "mark_to_market": mark_to_market,
        "total_pnl": total_pnl,
    }


def taker_cost_for_same_fills(trajectory: pd.DataFrame, fill_size: float) -> float:
    """What a taker would have paid, in real dollars, to cross the spread
    for the same number of real trades this maker's fills represent.

    Each individual taker trade costs half the spread relative to the
    real fair mid-price -- buying at the ask means paying half a spread
    above mid, selling at the bid means receiving half a spread below
    mid. A full round trip (one buy, one sell) therefore costs exactly
    one full spread -- the real mirror image of the maker's spread
    capture on the same round trip, using the real average spread
    actually quoted during the session.
    """
    if len(trajectory) == 0:
        raise ValueError("trajectory must not be empty")
    if fill_size <= 0:
        raise ValueError("fill_size must be positive")
    spread = trajectory["ask"] - trajectory["bid"]
    n_taker_trades = int(trajectory["bid_filled"].sum() + trajectory["ask_filled"].sum())
    avg_half_spread = float(spread.mean()) / 2
    return n_taker_trades * avg_half_spread * fill_size
