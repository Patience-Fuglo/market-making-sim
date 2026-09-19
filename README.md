# market-making-sim

Full event-driven market-making simulation, combining the real matching
engine (`orderbook-priority-sim`) and the real quoting/execution model
(`avellaneda-stoikov-calculator`) into one system: queue-aware fill
modeling, inventory skew, latency sensitivity, microstructure feature
engineering, and maker-vs-taker profitability.

## Status

| Module | Status |
|---|---|
| Queue-aware fill modeling | done |
| Inventory skew | done |
| Latency-sensitivity study | done |
| Microstructure feature engineering | not started |
| Maker-vs-taker profitability | not started |

## Queue-aware fill modeling

`src/market_making_sim/queue_fill.py`

Avellaneda-Stoikov tells you *what* price to quote. It says nothing
about whether that quote actually gets filled — in reality, a posted
quote joins a real queue at its price level (price-time priority), and
only fills as real trading activity works through everyone resting
ahead of it.

Real tick-by-tick order flow isn't freely available, so this uses real
intraday minute-level trading volume as the order-flow proxy instead —
honestly scoped to that real, coarser granularity rather than faking
tick-level precision. `participation_rate` (an illustrative design
parameter, same convention as `gamma`/`k` in
avellaneda-stoikov-calculator) is the assumed fraction of each real
minute's volume that trades through this specific quoted level.

```python
from market_making_sim import simulate_queue_fill

result = simulate_queue_fill(
    queue_ahead=50000, own_order_size=500,
    volume_trace=real_minute_volumes, participation_rate=0.1,
)
# {"filled": True, "fill_period": 3, "periods_to_fill": 4}
```

**Real result:** a real Avellaneda-Stoikov quote (bid $363.58 / ask
$364.88 on real TSLA data) simulated against real intraday minute volume
at three real queue positions — front of queue fills in 1 real minute,
a moderate queue (50,000 shares ahead) takes 4 real minutes, a deep
queue (800,000 shares ahead) takes 45 real minutes. Same quoted price,
very different real fill outcomes, driven entirely by queue position.

**A real data-quality catch along the way:** the real opening minute of
trading carried a massive volume spike (3.88M shares — a well-known real
auction-volume phenomenon), about 40x the real ~97k/minute average for
the rest of the day. Left in, it would have swamped all three queue
sizes into filling within that single atypical minute, hiding the real
effect this demo exists to show — excluded from the trace, with the
reasoning documented rather than silently dropped.

Run the real-data demo:

```bash
pip install -e .
python scripts/demo_queue_fill.py
```

Run the tests:

```bash
pytest tests/
```

## Dynamic inventory skew

`src/market_making_sim/inventory_skew.py`

Ties the reservation-price model and real price action together into a
feedback loop: at each real bar, the quote is recomputed from the market
maker's CURRENT inventory (not a single frozen snapshot), a real bid
fill is detected when the bar's real low reaches the quoted bid (and an
ask fill when the real high reaches the quoted ask), inventory updates,
and the next bar's quote reflects the new inventory — get filled buying,
the next quote skews down to attract sellers less and buyers more,
nudging the position back toward flat.

```python
from market_making_sim import simulate_inventory_trajectory

result = simulate_inventory_trajectory(
    price_bars=real_bars, initial_inventory=0, risk_aversion=0.5,
    volatility=0.03, order_arrival_sensitivity=1.5, fill_size=100,
)
```

**Real result:** replaying one real TSLA trading session (389 real
1-minute bars, opening print excluded), 33 real bid fills and 36 real
ask fills, inventory ranging from -500 to +500 shares and ending at
-300 — the self-correcting skew keeps it oscillating around flat rather
than running away in one direction. The `reservation_price` column
visibly diverges from `mid_price` as inventory builds (e.g. skewing
above mid while short), confirmed directly in the real output, not just
asserted.

Run the real-data demo:

```bash
python scripts/demo_inventory_skew.py
```

## Latency-sensitivity study

`src/market_making_sim/latency.py`

How much does a real delay between market information and your own
quote update actually cost? Real tick-by-tick data at microsecond
resolution isn't freely available, so this estimates the real expected
cost using a standard, well-founded technique: the expected magnitude of
a random-walk price move over a time window scales with the **square
root** of that window's length — the same scaling already used
elsewhere in this build (annualizing daily volatility). Given real,
observed annualized volatility, this converts a real latency window (10
microseconds, 50 microseconds, 1 millisecond) into a real, defensible
estimate of expected adverse price movement during that window.

```python
from market_making_sim import latency_sensitivity_study

result = latency_sensitivity_study(
    annualized_volatility=0.5134, mid_price=358.97,
    latency_values_seconds=[10e-6, 50e-6, 1e-3],
)
```

**Real result:** at real TSLA annualized volatility (51.34%), even a
full 1-millisecond latency window's expected adverse price move is only
~0.19% of the real quoted spread ($1.2909) — 10 microseconds is smaller
still (~0.02%). An honest finding, not a flattering assumption:
microsecond-scale latency, on its own, costs very little for a single
quote on a name like this. Latency arbitrage matters enormously in real
HFT because this tiny cost repeats across enormous trade volume and much
tighter-spread instruments (futures, FX) — not because any single
microsecond-scale window moves an equity's price by much on its own.

Run the real-data demo:

```bash
python scripts/demo_latency.py
```
