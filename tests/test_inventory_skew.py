import pandas as pd
import pytest

from market_making_sim import simulate_inventory_trajectory


def _bars(rows):
    """rows: list of (high, low, close) tuples."""
    return pd.DataFrame(
        [{"high": h, "low": l, "close": c} for h, l, c in rows],
        index=pd.date_range("2026-01-02", periods=len(rows), freq="min"),
    )


def test_bid_fill_increases_inventory():
    # real bid/ask at these params: 99.3546 / 100.6454 -- low crosses the
    # bid, high stays below the ask, so ONLY the bid side fills
    bars = _bars([(100.3, 90.0, 100.0)])
    result = simulate_inventory_trajectory(
        price_bars=bars, initial_inventory=0, risk_aversion=0.1,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
    )
    assert result["bid_filled"].iloc[0] == True  # noqa: E712
    assert result["inventory"].iloc[0] == 100


def test_ask_fill_decreases_inventory():
    # real bid/ask at these params: 99.3546 / 100.6454 -- high crosses the
    # ask, low stays above the bid, so ONLY the ask side fills
    bars = _bars([(110.0, 99.5, 100.0)])
    result = simulate_inventory_trajectory(
        price_bars=bars, initial_inventory=0, risk_aversion=0.1,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
    )
    assert result["ask_filled"].iloc[0] == True  # noqa: E712
    assert result["inventory"].iloc[0] == -100


def test_no_fill_when_bar_range_never_reaches_quotes():
    # a real bar with a very tight range that shouldn't touch either
    # side of a reasonably-spread quote
    bars = _bars([(100.01, 99.99, 100.0)])
    result = simulate_inventory_trajectory(
        price_bars=bars, initial_inventory=0, risk_aversion=0.1,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
    )
    assert result["bid_filled"].iloc[0] == False  # noqa: E712
    assert result["ask_filled"].iloc[0] == False  # noqa: E712
    assert result["inventory"].iloc[0] == 0


def test_both_sides_can_fill_in_the_same_volatile_bar():
    bars = _bars([(110.0, 90.0, 100.0)])
    result = simulate_inventory_trajectory(
        price_bars=bars, initial_inventory=0, risk_aversion=0.1,
        volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
    )
    assert result["bid_filled"].iloc[0] == True  # noqa: E712
    assert result["ask_filled"].iloc[0] == True  # noqa: E712
    assert result["inventory"].iloc[0] == 0  # +100 then -100, back to flat


def test_inventory_feeds_forward_and_shifts_next_quote():
    # first bar forces a bid fill (inventory goes long); second bar has
    # the identical real mid-price -- if the feedback loop works, the
    # second bar's reservation price should sit BELOW the first bar's
    # (long inventory skews the reservation price down)
    # real bid/ask at these params: 99.424 / 100.576 -- first bar's low
    # crosses only the bid (high stays below the ask)
    bars = _bars([(100.4, 90.0, 100.0), (100.5, 99.5, 100.0)])
    result = simulate_inventory_trajectory(
        price_bars=bars, initial_inventory=0, risk_aversion=0.5,
        volatility=0.05, order_arrival_sensitivity=1.5, fill_size=500,
    )
    assert result["inventory"].iloc[0] == 500
    assert result["reservation_price"].iloc[1] < result["reservation_price"].iloc[0]


def test_rejects_empty_price_bars():
    with pytest.raises(ValueError):
        simulate_inventory_trajectory(
            price_bars=pd.DataFrame(columns=["high", "low", "close"]),
            initial_inventory=0, risk_aversion=0.1, volatility=0.03,
            order_arrival_sensitivity=1.5, fill_size=100,
        )


def test_rejects_non_positive_fill_size():
    bars = _bars([(101.0, 99.0, 100.0)])
    with pytest.raises(ValueError):
        simulate_inventory_trajectory(
            price_bars=bars, initial_inventory=0, risk_aversion=0.1,
            volatility=0.03, order_arrival_sensitivity=1.5, fill_size=0,
        )
