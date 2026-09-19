"""Microstructure feature engineering: real order flow imbalance (OFI),
a short-term pressure signal for which way the price is likely to move
next, on top of the market maker's own inventory.

Real tick-level bid/ask size data isn't freely available, so this uses
the classic "tick rule" (Lee-Ready style) to classify each real bar's
volume as buyer- or seller-driven from real price movement alone: a real
bar's volume counts as buyer-driven if price rose from the prior real
bar, seller-driven if it fell -- a well-established, real trade-
classification technique, not fabricated order-flow data.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def classify_trade_direction(closes: pd.Series) -> pd.Series:
    """Tick-rule direction: +1 if price rose from the prior real bar
    (buyer-driven proxy), -1 if it fell (seller-driven), 0 if unchanged.
    The first real bar has no prior bar to compare against and is NaN.
    """
    diff = closes.diff()
    direction = np.sign(diff)
    return direction.rename("direction")


def order_flow_imbalance(closes: pd.Series, volumes: pd.Series, window: int) -> pd.Series:
    """Rolling real OFI: (buy volume - sell volume) / total volume over
    a trailing ``window`` of real bars. Ranges from -1 (all real recent
    volume seller-driven) to +1 (all buyer-driven); NaN wherever the
    window doesn't yet have ``window`` real bars of direction data, or
    total volume in the window is zero.
    """
    if window < 2:
        raise ValueError("window must be >= 2")
    direction = classify_trade_direction(closes)
    signed_volume = direction * volumes
    rolling_signed = signed_volume.rolling(window).sum()
    rolling_total = volumes.rolling(window).sum()
    ofi = rolling_signed / rolling_total.replace(0, np.nan)
    return ofi.rename(f"ofi_{window}")
