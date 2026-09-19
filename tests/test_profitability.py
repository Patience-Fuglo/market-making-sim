import pandas as pd
import pytest

from market_making_sim import compute_maker_pnl, taker_cost_for_same_fills


def _trajectory(rows):
    """rows: list of dicts with bid, ask, bid_filled, ask_filled, inventory, mid_price."""
    return pd.DataFrame(rows)


def test_maker_pnl_captures_spread_on_a_round_trip():
    # buy 10 at bid=99, sell 10 at ask=101 -- flat at the end, pure spread capture
    trajectory = _trajectory([
        {"bid": 99.0, "ask": 101.0, "bid_filled": True, "ask_filled": False, "inventory": 10, "mid_price": 100.0},
        {"bid": 99.0, "ask": 101.0, "bid_filled": False, "ask_filled": True, "inventory": 0, "mid_price": 100.0},
    ])
    result = compute_maker_pnl(trajectory, fill_size=10)
    assert result["n_bid_fills"] == 1
    assert result["n_ask_fills"] == 1
    # cash: -99*10 (buy) + 101*10 (sell) = 20
    assert result["realized_cash"] == pytest.approx(20.0)
    assert result["final_inventory"] == 0
    assert result["mark_to_market"] == pytest.approx(0.0)
    assert result["total_pnl"] == pytest.approx(20.0)


def test_maker_pnl_marks_leftover_inventory_to_final_mid_price():
    # only a bid fill -- ends the session long 10 shares, marked at real final mid
    trajectory = _trajectory([
        {"bid": 99.0, "ask": 101.0, "bid_filled": True, "ask_filled": False, "inventory": 10, "mid_price": 105.0},
    ])
    result = compute_maker_pnl(trajectory, fill_size=10)
    # cash: -99*10 = -990; mark-to-market: 10*105 = 1050; total: 60
    assert result["realized_cash"] == pytest.approx(-990.0)
    assert result["mark_to_market"] == pytest.approx(1050.0)
    assert result["total_pnl"] == pytest.approx(60.0)


def test_maker_pnl_leftover_inventory_can_hurt_if_price_falls():
    trajectory = _trajectory([
        {"bid": 99.0, "ask": 101.0, "bid_filled": True, "ask_filled": False, "inventory": 10, "mid_price": 90.0},
    ])
    result = compute_maker_pnl(trajectory, fill_size=10)
    # cash: -990; mark-to-market: 10*90=900; total: -90 -- a real loss on unsold inventory
    assert result["total_pnl"] == pytest.approx(-90.0)


def test_maker_pnl_rejects_empty_trajectory():
    with pytest.raises(ValueError):
        compute_maker_pnl(pd.DataFrame(columns=["bid", "ask", "bid_filled", "ask_filled", "inventory", "mid_price"]), fill_size=10)


def test_maker_pnl_rejects_non_positive_fill_size():
    trajectory = _trajectory([
        {"bid": 99.0, "ask": 101.0, "bid_filled": True, "ask_filled": False, "inventory": 10, "mid_price": 100.0},
    ])
    with pytest.raises(ValueError):
        compute_maker_pnl(trajectory, fill_size=0)


def test_taker_cost_is_the_mirror_image_of_maker_spread_capture():
    trajectory = _trajectory([
        {"bid": 99.0, "ask": 101.0, "bid_filled": True, "ask_filled": False, "inventory": 10, "mid_price": 100.0},
        {"bid": 99.0, "ask": 101.0, "bid_filled": False, "ask_filled": True, "inventory": 0, "mid_price": 100.0},
    ])
    maker_result = compute_maker_pnl(trajectory, fill_size=10)
    taker_result = taker_cost_for_same_fills(trajectory, fill_size=10)
    # same 2 trades, same real $2 spread each, size 10 -- taker's real cost
    # should equal exactly what the maker captured on this flat round trip
    assert taker_result == pytest.approx(maker_result["realized_cash"])
