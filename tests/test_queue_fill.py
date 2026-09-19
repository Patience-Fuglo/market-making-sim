import pytest

from market_making_sim import simulate_queue_fill


def test_fills_immediately_when_no_queue_ahead_and_enough_volume():
    result = simulate_queue_fill(
        queue_ahead=0, own_order_size=100, volume_trace=[2000], participation_rate=0.1
    )
    # available in period 0: 2000*0.1 = 200 >= 100 own order
    assert result["filled"] is True
    assert result["fill_period"] == 0
    assert result["periods_to_fill"] == 1


def test_queue_ahead_must_be_consumed_before_own_order_can_fill():
    # period 0: 1000*0.1=100 available, all consumed by the queue ahead (150 needed)
    # period 1: 1000*0.1=100 available, 50 finishes the queue, 50 left for own order
    # period 2: 1000*0.1=100 available, fills the remaining 50 of the own order
    result = simulate_queue_fill(
        queue_ahead=150, own_order_size=100, volume_trace=[1000, 1000, 1000], participation_rate=0.1
    )
    assert result["filled"] is True
    assert result["fill_period"] == 2


def test_never_fills_if_volume_trace_runs_out_first():
    result = simulate_queue_fill(
        queue_ahead=1000, own_order_size=100, volume_trace=[10, 10, 10], participation_rate=0.1
    )
    assert result["filled"] is False
    assert result["fill_period"] is None
    assert result["periods_to_fill"] is None


def test_larger_queue_ahead_takes_longer_or_fails_to_fill():
    small_queue = simulate_queue_fill(queue_ahead=50, own_order_size=50, volume_trace=[100] * 10, participation_rate=0.1)
    large_queue = simulate_queue_fill(queue_ahead=500, own_order_size=50, volume_trace=[100] * 10, participation_rate=0.1)
    assert small_queue["filled"] is True
    # larger queue either takes strictly longer, or fails to fill within the same trace
    assert large_queue["filled"] is False or large_queue["periods_to_fill"] > small_queue["periods_to_fill"]


def test_rejects_negative_queue_ahead():
    with pytest.raises(ValueError):
        simulate_queue_fill(queue_ahead=-1, own_order_size=10, volume_trace=[100])


def test_rejects_non_positive_own_order_size():
    with pytest.raises(ValueError):
        simulate_queue_fill(queue_ahead=0, own_order_size=0, volume_trace=[100])


def test_rejects_out_of_range_participation_rate():
    with pytest.raises(ValueError):
        simulate_queue_fill(queue_ahead=0, own_order_size=10, volume_trace=[100], participation_rate=1.5)
    with pytest.raises(ValueError):
        simulate_queue_fill(queue_ahead=0, own_order_size=10, volume_trace=[100], participation_rate=0.0)
