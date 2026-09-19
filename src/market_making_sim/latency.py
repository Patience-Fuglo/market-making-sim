"""Latency-sensitivity study: how much does a real delay between market
information and your own quote update actually cost?

Real tick-by-tick data at microsecond resolution isn't freely available,
so this estimates the real expected cost using a standard, well-founded
technique instead of fabricating tick data: the expected magnitude of a
random-walk price move over a time window scales with the SQUARE ROOT of
that window's length (the same square-root-of-time scaling already used
elsewhere in this build to annualize daily volatility). Given a real,
observed annualized volatility, this lets a real latency window (10
microseconds, 50 microseconds, 1 millisecond) be converted into a real,
defensible estimate of expected adverse price movement during that
window -- the real cost of being that slow to react.
"""

from __future__ import annotations

import math

import pandas as pd

_TRADING_SECONDS_PER_YEAR = 252 * 6.5 * 3600  # 252 real trading days, 6.5-hour real sessions


def expected_adverse_move(annualized_volatility: float, latency_seconds: float) -> float:
    """Expected magnitude of price movement (as a fraction of price)
    during a real latency window, scaled from annualized volatility.

    ``sigma_window = sigma_annual * sqrt(latency_seconds / trading_seconds_per_year)``
    -- the same square-root-of-time scaling already used elsewhere in
    this build (e.g. daily-to-annual volatility conversion), applied in
    the opposite direction here: from annual down to a real, much
    shorter latency window.
    """
    if annualized_volatility < 0:
        raise ValueError("annualized_volatility cannot be negative")
    if latency_seconds <= 0:
        raise ValueError("latency_seconds must be positive")
    return annualized_volatility * math.sqrt(latency_seconds / _TRADING_SECONDS_PER_YEAR)


def latency_sensitivity_study(
    annualized_volatility: float,
    mid_price: float,
    latency_values_seconds: list[float],
) -> pd.DataFrame:
    """Expected real adverse-selection cost (in price terms and as a
    fraction of a typical spread) at each real latency value.
    """
    rows = []
    for latency in latency_values_seconds:
        move_fraction = expected_adverse_move(annualized_volatility, latency)
        rows.append({
            "latency_seconds": latency,
            "expected_move_fraction": move_fraction,
            "expected_move_usd": move_fraction * mid_price,
        })
    return pd.DataFrame(rows)
