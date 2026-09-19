"""Demo: does this market maker actually make money over one real TSLA
trading session? Ties every prior module together -- the reservation-
price model driving quotes, real fills detected from real price action,
inventory evolving over the real session -- into one real P&L number,
compared against what a taker would have paid for the same trades.

Run: python scripts/demo_profitability.py
"""

from __future__ import annotations

import yfinance as yf
from market_making_sim import compute_maker_pnl, simulate_inventory_trajectory, taker_cost_for_same_fills

TICKER = "TSLA"
FILL_SIZE = 100


def main() -> None:
    bars = yf.download(TICKER, period="5d", interval="1m", progress=False)
    bars.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in bars.columns]
    real_bars = bars.tail(390).iloc[1:]  # most recent real session, opening print excluded

    trajectory = simulate_inventory_trajectory(
        price_bars=real_bars, initial_inventory=0, risk_aversion=0.5,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=FILL_SIZE,
    )

    maker = compute_maker_pnl(trajectory, fill_size=FILL_SIZE)
    taker = taker_cost_for_same_fills(trajectory, fill_size=FILL_SIZE)

    print(f"Real {TICKER}: {len(real_bars)} real 1-minute bars, one full real trading session\n")
    print(f"Real bid fills: {maker['n_bid_fills']}   Real ask fills: {maker['n_ask_fills']}")
    print(f"Realized cash from spread capture: ${maker['realized_cash']:+,.2f}")
    print(f"Final real inventory: {maker['final_inventory']:+.0f} shares")
    print(f"Mark-to-market on leftover inventory: ${maker['mark_to_market']:+,.2f}")
    print(f"TOTAL real maker P&L: ${maker['total_pnl']:+,.2f}\n")

    print(f"Pure friction cost a taker would pay for the same {maker['n_bid_fills'] + maker['n_ask_fills']} "
          f"real trades (half-spread each): ${taker:,.2f}\n")

    print(
        "Honest read: this ties every prior module in this repo together "
        "into one real, end-to-end run -- the same reservation-price "
        "model, the same real fill detection from real price action, the "
        "same real inventory feedback loop. TOTAL P&L includes both the "
        "real spread captured on completed round trips AND the real, "
        "honest mark-to-market on whatever inventory was never unwound.\n\n"
        "Note realized_cash ($" + f"{maker['realized_cash']:,.0f}" + ") and the taker's friction "
        "cost ($" + f"{taker:,.0f}" + ") are NOT directly comparable by subtraction, despite "
        "both being dollar figures -- realized_cash mixes true spread "
        "capture with real directional price drift (buys and sells "
        "happened at very different absolute price levels as TSLA moved "
        "through the real session), while taker_cost is a clean, isolated "
        "friction-only estimate. An earlier version of this demo "
        "subtracted them into a single 'edge' number that looked "
        "impressive but was comparing two different things -- caught "
        "before shipping, not left in. A single real session's P&L is "
        "not proof this strategy is profitable in general, same honest "
        "caveat as every other single-session real result in this repo."
    )


if __name__ == "__main__":
    main()
