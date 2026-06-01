# P2 Backtest Telemetry — Narrative Report

## What P2 Added

P2 wired telemetry recording into the backtest loop. Every time a strategy processes
a price bar, it now emits a JSON snapshot to disk. You can replay the full history of
strategy state after a backtest finishes — no need to rerun to answer "what was the
RSI reading at bar 200?" or "when did the strategy flip to sell?".

The new class is `BacktestTelemetry` (in `alpha_kd/backtest_telemetry.py`). It takes
the same arguments as the legacy `Quantreo.Backtest` but adds two things:

1. A `TelemetryBuffer` that appends one JSON line per bar to a `.jsonl` file.
2. Each line includes the base strategy state (`side`, `entry_price`,
   `unrealized_pnl`, `signal`, `timestamp`) plus three P2-specific keys:
   `bar_time`, `entry_signal`, and `exit_return`.

The legacy `Quantreo/Backtest.py` was **not modified** — zero changes to the legacy
core. `BacktestTelemetry` directly instantiates the strategy and runs its own loop.

## How to Verify It Works

```bash
# 1. Import check
python -c "from alpha_kd import BacktestTelemetry; print(BacktestTelemetry)"
# Expected: <class 'alpha_kd.backtest_telemetry.BacktestTelemetry'>

# 2. Run tests
pytest tests/test_backtest_telemetry.py -v
# Expected: 2 passed

# 3. Full suite
pytest -q
# Expected: all tests pass

# 4. CLI flag
python -m alpha_kd --backtest
# Expected: "Backtest telemetry mode — not yet wired to live data."

# 5. Lint
python -m ruff check alpha_kd/ tests/ --select E,W,F
# Expected: All checks passed!
```

## Architecture

```
User script
    │
    └─► BacktestTelemetry(data, RsiSma, params, telemetry_path=Path("out.jsonl"))
              │
              ├─ self.strategy = RsiSma(data, params)          ← alpha_kd Strategy
              └─ self.buffer   = TelemetryBuffer(path)         ← P1.5 ring buffer
                       │
                       └─ BacktestTelemetry.run()
                               │
                               for bar in strategy.data.index:
                                   entry_signal = strategy.get_entry_signal(bar)
                                   exit_ret     = strategy.get_exit_signal(bar)
                                   state        = strategy.get_state()
                                   state["bar_time"]     = bar
                                   state["entry_signal"] = entry_signal
                                   state["exit_return"]  = exit_ret
                                   buffer.record(state)   ── append JSON line
```

## What Comes Next (P3)

- **Live data fetcher** — plug Yahoo Finance or Upstox historical API into
  `BacktestTelemetry` so the CLI `--backtest` flag can run a real backtest
  without writing a script.
- **Regime-aware strategy variant** (`RsiSmaRegime`) — combine P1.5 `get_state()`
  output with a regime label from `MarketDownRegimeAnalyzer` per bar.
- **Dashboard** — stream the `.jsonl` file into a lightweight web UI for
  interactive post-hoc replay.
