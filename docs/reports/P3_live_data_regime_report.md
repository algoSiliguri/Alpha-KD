# P3 Live Data + Regime-Aware Strategy — Narrative Report

## What P3 Added

Phase 3 wired Alpha-KD from synthetic test data to real market data, and upgraded
the core strategy with a Hidden Markov Model (HMM) regime detector.

**Four concrete additions:**

1. **`yfinance` dependency** (`pyproject.toml`) — enables downloading historical
   OHLCV bars directly from Yahoo Finance without a broker account.

2. **`YahooFinanceFetcher`** (`alpha_kd/data_fetcher.py`) — thin I/O class that:
   - Downloads bars via `yf.Ticker.history(period, interval)`
   - Normalises column names to lowercase (e.g. `Close` → `close`)
   - Caches results to `Data/<symbol>_<interval>_<period>.csv` so repeated runs
     don't hit the network
   - Adds `high_time`/`low_time` placeholder columns (`NaT`) required by the
     `RsiSma` exit-signal logic

3. **`RsiSmaRegime`** (`alpha_kd/strategies/rsi_sma_regime.py`) — extends `RsiSma`
   with a 3-state Gaussian HMM fitted on per-bar log-returns. On construction:
   - Fits the HMM with `n_components=3` (bear / sideways / bull)
   - Maps the last bar's predicted state to a human-readable label
   - Exposes the label via `get_state()["regime"]`
   - Falls back to `"unknown"` on any fitting failure or insufficient data (<30 bars)

4. **Wired CLI** (`alpha_kd/__main__.py`) — `python -m alpha_kd --backtest` now:
   - Fetches 5 days of hourly AAPL bars via `YahooFinanceFetcher`
   - Runs the full per-bar entry/exit loop via `BacktestTelemetry`
   - Prints bar count and last recorded state on completion

---

## How to Verify

```bash
# 1. Import check
python3 -c "
from alpha_kd.data_fetcher import YahooFinanceFetcher
from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime
print('imports ok')
"

# 2. Run the backtest CLI
python3 -m alpha_kd --backtest
# Expected output: "Backtest complete: N bars"

# 3. Inspect cached data
ls Data/AAPL_1h_5d.csv

# 4. Read telemetry
python3 -m alpha_kd --state

# 5. Full test suite
pytest -q

# 6. Lint
ruff check alpha_kd/ tests/ --select E,W,F
```

---

## Architecture

```
Yahoo Finance API
       │
       ▼
YahooFinanceFetcher.fetch()
  └── caches to Data/AAPL_1h_5d.csv
       │
       ▼ pd.DataFrame (OHLCV + high_time/low_time placeholders)
       │
       ▼
RsiSmaRegime(data, params)
  ├── RsiSma.get_features()   — SMA + RSI signals
  ├── RsiSma.get_entry_signal()
  ├── RsiSma.get_exit_signal()
  └── _fit_regime()           — 3-state HMM → "bull"/"bear"/"sideways"/"unknown"
       │
       ▼
BacktestTelemetry.run()
  └── per-bar loop → get_state() → TelemetryBuffer → telemetry.jsonl
       │
       ▼
stdout: "Backtest complete: N bars"
        "Last state: {side, entry_price, regime, ...}"
```

---

## What Comes Next (P4)

- **Multi-symbol support** — loop over a ticker list, aggregate telemetry
- **Dashboard** — stream telemetry.jsonl into a real-time Streamlit view
- **Paper trading** — plug `YahooFinanceFetcher` into a live polling loop
  (Upstox or MT5) with throttled refresh
- **Walk-forward validation** — run `RsiSmaRegime` through
  `CombinatorialPurgedCV` to validate regime labels aren't look-ahead biased
