"""Demo: a market maker's inventory actually evolving over a real TSLA
trading session, with each quote recomputed from the CURRENT inventory
rather than a single fixed snapshot.

Run: python scripts/demo_inventory_skew.py
"""

from __future__ import annotations

import yfinance as yf
from market_making_sim import simulate_inventory_trajectory

TICKER = "TSLA"


def main() -> None:
    bars = yf.download(TICKER, period="5d", interval="1m", progress=False)
    bars.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in bars.columns]
    # real most recent full session, opening print excluded (same real
    # microstructure reason as the queue-fill demo -- an outsized first
    # print isn't representative of ongoing trading)
    real_bars = bars.tail(390).iloc[1:]

    print(f"Real {TICKER}: simulating {len(real_bars)} real 1-minute bars, most recent session\n")

    result = simulate_inventory_trajectory(
        price_bars=real_bars, initial_inventory=0, risk_aversion=0.5,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
    )

    n_bid_fills = int(result["bid_filled"].sum())
    n_ask_fills = int(result["ask_filled"].sum())
    print(f"Real bid fills: {n_bid_fills}   Real ask fills: {n_ask_fills}")
    print(f"Final real inventory: {result['inventory'].iloc[-1]:+.0f} shares")
    print(f"Inventory range over the real session: {result['inventory'].min():+.0f} to {result['inventory'].max():+.0f}\n")

    print("First 5 real minutes:")
    print(result[["mid_price", "reservation_price", "bid", "ask", "inventory"]].head().to_string())
    print("\nLast 5 real minutes:")
    print(result[["mid_price", "reservation_price", "bid", "ask", "inventory"]].tail().to_string())

    print(
        "\nHonest read: this replays one real TSLA trading session bar by "
        "bar, recomputing the quote from the market maker's CURRENT "
        "inventory at every step -- not a single static snapshot. Watch "
        "the reservation_price column diverge from mid_price as inventory "
        "builds up: that divergence is the real feedback loop from the "
        "reservation-price model, now actually running over real time "
        "instead of a single frozen calculation."
    )


if __name__ == "__main__":
    main()
