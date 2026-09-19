import numpy as np
import pandas as pd
import pytest

from market_making_sim import classify_trade_direction, order_flow_imbalance


def _series(values):
    return pd.Series(values, index=pd.date_range("2026-01-02", periods=len(values), freq="min"))


def test_classify_trade_direction_marks_rises_as_positive():
    closes = _series([100.0, 101.0, 102.0])
    direction = classify_trade_direction(closes)
    assert direction.iloc[1] == 1.0
    assert direction.iloc[2] == 1.0


def test_classify_trade_direction_marks_falls_as_negative():
    closes = _series([100.0, 99.0, 98.0])
    direction = classify_trade_direction(closes)
    assert direction.iloc[1] == -1.0
    assert direction.iloc[2] == -1.0


def test_classify_trade_direction_first_bar_is_nan():
    closes = _series([100.0, 101.0])
    direction = classify_trade_direction(closes)
    assert np.isnan(direction.iloc[0])


def test_classify_trade_direction_unchanged_price_is_zero():
    closes = _series([100.0, 100.0])
    direction = classify_trade_direction(closes)
    assert direction.iloc[1] == 0.0


def test_ofi_is_fully_positive_when_all_volume_is_buyer_driven():
    closes = _series([100.0, 101.0, 102.0, 103.0])
    volumes = _series([1000, 1000, 1000, 1000])
    ofi = order_flow_imbalance(closes, volumes, window=3)
    assert ofi.iloc[-1] == pytest.approx(1.0)


def test_ofi_is_fully_negative_when_all_volume_is_seller_driven():
    closes = _series([100.0, 99.0, 98.0, 97.0])
    volumes = _series([1000, 1000, 1000, 1000])
    ofi = order_flow_imbalance(closes, volumes, window=3)
    assert ofi.iloc[-1] == pytest.approx(-1.0)


def test_ofi_is_near_zero_when_buy_and_sell_volume_are_balanced():
    # up, down, up, down -- equal volume each bar -> balanced OFI
    closes = _series([100.0, 101.0, 100.0, 101.0, 100.0])
    volumes = _series([1000, 1000, 1000, 1000, 1000])
    ofi = order_flow_imbalance(closes, volumes, window=4)
    assert ofi.iloc[-1] == pytest.approx(0.0, abs=1e-9)


def test_ofi_weights_by_real_volume_not_just_bar_count():
    # 1 big up bar + 1 small down bar -- OFI should skew positive since
    # the up bar carries far more real volume
    closes = _series([100.0, 101.0, 100.5])
    volumes = _series([1000, 9000, 100])
    ofi = order_flow_imbalance(closes, volumes, window=2)
    assert ofi.iloc[-1] > 0.5


def test_ofi_rejects_window_below_two():
    closes = _series([100.0, 101.0])
    volumes = _series([100, 100])
    with pytest.raises(ValueError):
        order_flow_imbalance(closes, volumes, window=1)
