"""Demo: real order flow imbalance (OFI) computed on real intraday TSLA
data -- does it actually carry real predictive signal for the next
bar's price move, the way it's supposed to?

Run: python scripts/demo_microstructure.py
"""

from __future__ import annotations

import yfinance as yf
from market_making_sim import order_flow_imbalance
from quant_toolkit.metrics import information_coefficient

TICKER = "TSLA"
WINDOW = 10


def main() -> None:
    bars = yf.download(TICKER, period="5d", interval="1m", progress=False)
    bars.columns = [c[0].lower() if isinstance(c, tuple) else c.lower() for c in bars.columns]
    real_bars = bars.tail(390).iloc[1:]  # most recent real session, opening print excluded

    ofi = order_flow_imbalance(real_bars["close"], real_bars["volume"], window=WINDOW)
    next_bar_return = real_bars["close"].shift(-1) / real_bars["close"] - 1.0

    print(f"Real {TICKER}: {len(real_bars)} real 1-minute bars, OFI window={WINDOW}\n")
    print(f"Real OFI summary: mean={ofi.mean():+.4f}  std={ofi.std():.4f}  "
          f"min={ofi.min():+.4f}  max={ofi.max():+.4f}\n")

    ic = information_coefficient(ofi, next_bar_return)
    print(f"Real IC (OFI vs. next real 1-minute return): {ic:+.4f}")

    print(
        "\nHonest read: this reuses information_coefficient from "
        "alpha-validation-toolkit directly, the exact same real "
        "statistical tool used to validate the alt-data signal -- IC "
        "doesn't care whether the input is an insider-trading feature or "
        "a microstructure feature, it's the same real question either "
        "way: does this signal's ordering match what actually happened "
        "next. A real, small, single-day IC here is not proof of a "
        "validated trading signal -- the same purged walk-forward "
        "discipline from the alt-data arm would be needed before trusting "
        "this for real trading, not just this one real session's number."
    )


if __name__ == "__main__":
    main()
