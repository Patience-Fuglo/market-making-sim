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
| Microstructure feature engineering | done |
| Maker-vs-taker profitability | done |

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

## Microstructure feature engineering

`src/market_making_sim/microstructure.py`

Order flow imbalance (OFI): a short-term pressure signal for which way
the price is likely to move next, on top of the market maker's own
inventory. Real tick-level bid/ask size data isn't freely available, so
this uses the classic "tick rule" (Lee-Ready style) to classify each
real bar's volume as buyer- or seller-driven from real price movement
alone — a well-established, real trade-classification technique, not
fabricated order-flow data.

```python
from market_making_sim import order_flow_imbalance

ofi = order_flow_imbalance(real_bars["close"], real_bars["volume"], window=10)
```

**Real result:** OFI computed on one real TSLA trading session (389 real
1-minute bars) scores a real IC of **+0.11** against the next real
1-minute return, reusing `information_coefficient` directly from
`alpha-validation-toolkit` — the exact same real statistical tool used
to validate the alt-data signal, applied here to a microstructure
feature instead. A real, positive single-session IC is not proof of a
validated trading signal on its own — the same purged walk-forward
discipline from the alt-data arm would be needed before trusting this
for real trading.

Run the real-data demo:

```bash
python scripts/demo_microstructure.py
```

## Maker-vs-taker profitability

`src/market_making_sim/profitability.py`

Ties every prior module in this repo into one real, end-to-end run: the
reservation-price model driving quotes, real fills detected from real
price action, inventory evolving over the real session — into one real
P&L number. A maker's profit comes from the spread, captured repeatedly;
the real risk is being left holding unsold inventory, marked to the real
final price.

```python
from market_making_sim import compute_maker_pnl, simulate_inventory_trajectory, taker_cost_for_same_fills

trajectory = simulate_inventory_trajectory(...)
maker = compute_maker_pnl(trajectory, fill_size=100)
taker = taker_cost_for_same_fills(trajectory, fill_size=100)
```

**A real bug caught before it reached the committed code:** the first
draft of `compute_maker_pnl` summed fill *prices* without multiplying by
trade size — correct only for a 1-share fill. Fixed before any test was
written against it. **A second, conceptual bug caught in the demo
script:** an early version subtracted `taker_cost` from `realized_cash`
to report a single "edge" number. Real result showed this was comparing
two different things — `realized_cash` mixes true spread capture with
real directional price drift (fills happen at very different absolute
price levels as the real session moves), while `taker_cost` is a clean,
isolated friction-only estimate (half the spread per trade, the real
mirror image of what a maker captures on a matched round trip). The
subtraction was removed; both numbers are reported honestly side by
side instead.

**Real result:** one real TSLA session, 33 bid fills, 36 ask fills,
+$114,463 realized cash from spread capture, a real -$109,269
mark-to-market loss on the -300 shares left unsold at session end,
netting to a real **+$5,194** total P&L. A taker doing the same 69 real
trades would have paid a real $3,971 in pure friction cost. A single
real session's P&L is not proof this strategy is profitable in general
— same honest caveat as every other single-session result in this repo.

Run the real-data demo:

```bash
python scripts/demo_profitability.py
```
