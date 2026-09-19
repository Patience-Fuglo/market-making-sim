import math

import pytest

from market_making_sim import expected_adverse_move, latency_sensitivity_study


def test_expected_adverse_move_scales_with_sqrt_of_latency():
    # quadrupling the latency window should double the expected move
    # (sqrt-of-time scaling)
    move_1x = expected_adverse_move(annualized_volatility=0.5, latency_seconds=0.001)
    move_4x = expected_adverse_move(annualized_volatility=0.5, latency_seconds=0.004)
    assert move_4x == pytest.approx(2 * move_1x)


def test_expected_adverse_move_scales_linearly_with_volatility():
    move_low = expected_adverse_move(annualized_volatility=0.2, latency_seconds=0.001)
    move_high = expected_adverse_move(annualized_volatility=0.4, latency_seconds=0.001)
    assert move_high == pytest.approx(2 * move_low)


def test_expected_adverse_move_matches_hand_computed_value():
    trading_seconds_per_year = 252 * 6.5 * 3600
    sigma, latency = 0.46, 0.001  # ~real TSLA annualized vol, 1ms
    expected = sigma * math.sqrt(latency / trading_seconds_per_year)
    actual = expected_adverse_move(sigma, latency)
    assert actual == pytest.approx(expected, rel=1e-9)


def test_expected_adverse_move_rejects_negative_volatility():
    with pytest.raises(ValueError):
        expected_adverse_move(-0.1, 0.001)


def test_expected_adverse_move_rejects_non_positive_latency():
    with pytest.raises(ValueError):
        expected_adverse_move(0.3, 0.0)


def test_1ms_is_ten_times_10_microseconds():
    # 1ms / 10us = 100 -> sqrt(100) = 10x the expected move
    move_10us = expected_adverse_move(0.46, 10e-6)
    move_1ms = expected_adverse_move(0.46, 1e-3)
    assert move_1ms == pytest.approx(10 * move_10us, rel=1e-9)


def test_latency_sensitivity_study_returns_one_row_per_value():
    result = latency_sensitivity_study(
        annualized_volatility=0.46, mid_price=365.0,
        latency_values_seconds=[10e-6, 50e-6, 1e-3],
    )
    assert len(result) == 3
    assert list(result.columns) == ["latency_seconds", "expected_move_fraction", "expected_move_usd"]
    assert result["expected_move_usd"].is_monotonic_increasing
