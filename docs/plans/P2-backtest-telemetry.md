# P2: Backtesting Harness Telemetry Integration

> **For Claude Code:** Use subagent-driven-development skill to implement this plan task-by-task.  
> **Branch:** `feature/p2-backtest-telemetry`

**Goal:** Wire `TelemetryBuffer.record()` into the legacy backtest loop so every bar produces a state snapshot, enabling post-hoc replay and regime attribution.

**Architecture:** A thin `BacktestTelemetry` adapter wraps the existing `Quantreo.Backtest` class. It injects one `TelemetryBuffer.record()` call at the end of each bar iteration. The adapter lives in `alpha_kd/` (P1.5 territory) and delegates to `Quantreo/` (legacy). Zero changes to legacy backtest core logic.

**Tech Stack:** Python 3.11, stdlib `json`/`pathlib` only for new code, pandas for existing backtest.

---

## Context

P1.5 gave every strategy a `get_state()` hook and a `TelemetryBuffer` ring buffer. But nothing calls them yet. The legacy `Quantreo.Backtest` has a `run()` loop that iterates over `self.data.index` and calls `get_entry_signal` and `get_exit_signal` per bar. This is the natural injection point.

We do NOT refactor `Quantreo/Backtest.py` (legacy, 172 lines, out of scope). We wrap it.

---

## Execution Checklist

### Task 1: Create `BacktestTelemetry` adapter stub

**Objective:** Add a new file `alpha_kd/backtest_telemetry.py` that wraps `Quantreo.Backtest` and injects telemetry recording.

**Files:**
- Create: `alpha_kd/backtest_telemetry.py`
- Test: `tests/test_backtest_telemetry.py`

**Step 1: Write the adapter (≤70 lines)**

```python
"""Thin adapter: wraps Quantreo.Backtest and records state per bar into TelemetryBuffer."""
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from alpha_kd.telemetry import TelemetryBuffer
from Quantreo.Backtest import Backtest


class BacktestTelemetry:
    """Wraps Backtest.run() and persists strategy.get_state() at every bar."""

    def __init__(
        self,
        data: pd.DataFrame,
        TradingStrategy: Any,
        parameters: Dict[str, Any],
        initial_capital: int = 100_000,
        telemetry_path: Optional[Path] = None,
        max_records: int = 10_000,
    ):
        self.backtest = Backtest(data, TradingStrategy, parameters, initial_capital)
        path = telemetry_path or Path("telemetry.jsonl")
        self.buffer = TelemetryBuffer(path, max_records=max_records)

    def run(self) -> None:
        """Execute backtest loop and record state after every bar."""
        for current_time in self.backtest.data.index:
            # Delegate to the wrapped backtest's entry/exit logic
            entry_signal, self.backtest.entry_trade_time = (
                self.backtest.TradingStrategy.get_entry_signal(current_time)
            )
            exit_ret, self.backtest.exit_trade_time = (
                self.backtest.TradingStrategy.get_exit_signal(current_time)
            )

            # Record state snapshot
            state = self.backtest.TradingStrategy.get_state()
            state["bar_time"] = str(current_time)
            state["entry_signal"] = entry_signal
            state["exit_return"] = exit_ret if exit_ret else 0.0
            self.buffer.record(state)
```

**Rules:**
- Do not modify `Quantreo/Backtest.py`.
- `BacktestTelemetry` delegates per-bar logic to the wrapped backtest.
- State dict adds three extra keys: `bar_time`, `entry_signal`, `exit_return`.
- File must be ≤70 lines.

---

### Task 2: Add `BacktestTelemetry` to package exports

**Objective:** Make `BacktestTelemetry` importable from `alpha_kd`.

**Files:**
- Modify: `alpha_kd/__init__.py`

**Step 1: Append export**

```python
from alpha_kd.backtest_telemetry import BacktestTelemetry

__all__.append("BacktestTelemetry")
```

**Verification:**
```bash
python -c "from alpha_kd import BacktestTelemetry; print(BacktestTelemetry)"
```
Expected: `<class 'alpha_kd.backtest_telemetry.BacktestTelemetry'>`

**Commit:**
```bash
git add alpha_kd/__init__.py
git commit -m "feat: export BacktestTelemetry from alpha_kd"
```

---

### Task 3: Write tests for `BacktestTelemetry`

**Objective:** Prove that `BacktestTelemetry.run()` records the expected number of state snapshots.

**Files:**
- Create: `tests/test_backtest_telemetry.py`

**Step 1: Write failing test**

```python
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alpha_kd.backtest_telemetry import BacktestTelemetry
from alpha_kd.strategies.rsi_sma import RsiSma


@pytest.fixture
def sample_df():
    dates = pd.date_range("2023-01-01", periods=50, freq="h")
    rng = np.random.default_rng(42)
    close = 1.0 + rng.standard_normal(50).cumsum() * 0.01
    delta = rng.standard_normal(50) * 0.005
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + np.abs(delta),
            "low": close - np.abs(delta),
            "close": close,
        },
        index=dates,
    )
    df["high_time"] = df.index
    df["low_time"] = df.index
    return df


@pytest.fixture
def params():
    return {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }


def test_backtest_telemetry_records_all_bars(sample_df, params):
    with tempfile.TemporaryDirectory() as tmp:
        tel_path = Path(tmp) / "telemetry.jsonl"
        bt = BacktestTelemetry(
            sample_df, RsiSma, params, telemetry_path=tel_path, max_records=10_000
        )
        bt.run()
        lines = tel_path.read_text().splitlines()
        assert len(lines) == len(sample_df)


def test_backtest_telemetry_state_keys(sample_df, params):
    with tempfile.TemporaryDirectory() as tmp:
        tel_path = Path(tmp) / "telemetry.jsonl"
        bt = BacktestTelemetry(
            sample_df, RsiSma, params, telemetry_path=tel_path
        )
        bt.run()
        state = bt.buffer.tail(1)[0]
        assert "bar_time" in state
        assert "entry_signal" in state
        assert "exit_return" in state
        assert "side" in state
```

**Step 2: Run to verify failure**
```bash
pytest tests/test_backtest_telemetry.py -v
```
Expected: FAIL — `BacktestTelemetry` not yet implemented or `Quantreo` import missing.

**Step 3: Check `PYTHONPATH`**
If `Quantreo` import fails in CI, append `sys.path` in the test or adjust `pyproject.toml`.

---

### Task 4: Update CLI with `--backtest` flag

**Objective:** Let the CLI run a minimal backtest and dump telemetry.

**Files:**
- Modify: `alpha_kd/__main__.py`

**Step 1: Add argument and handler**

```python
parser.add_argument(
    "--backtest",
    action="store_true",
    help="Run a minimal backtest and print telemetry summary",
)
```

```python
if args.backtest:
    print("Backtest telemetry mode — not yet wired to live data.")
    print("Use BacktestTelemetry(adapter) in scripts for now.")
```

**Rules:**
- No live data fetching in CLI yet (P3 scope).
- Print a helpful message directing users to the adapter.

**Verification:**
```bash
python -m alpha_kd --backtest
```
Expected: `Backtest telemetry mode — not yet wired to live data.`

**Commit:**
```bash
git add alpha_kd/__main__.py
git commit -m "feat: add --backtest CLI flag (stub)"
```

---

### Task 5: Narrative report

**Objective:** Write `docs/reports/P2_backtest_telemetry_report.md`.

**Files:**
- Create: `docs/reports/P2_backtest_telemetry_report.md`

**Required sections:**
- What P2 added (plain English)
- How to verify it works (copy-paste commands)
- Architecture diagram (ASCII bullet list)
- What comes next (P3 — live data fetcher or regime-aware strategy variant)

**Commit:**
```bash
git add docs/reports/P2_backtest_telemetry_report.md
git commit -m "docs: add P2 narrative report"
```

---

## Success Criteria

- [ ] `BacktestTelemetry.run()` records exactly `len(df)` state snapshots.
- [ ] Each snapshot contains keys: `side`, `entry_price`, `unrealized_pnl`, `signal`, `timestamp`, `bar_time`, `entry_signal`, `exit_return`.
- [ ] `pytest tests/test_backtest_telemetry.py -v` passes.
- [ ] `python -c "from alpha_kd import BacktestTelemetry"` works.
- [ ] `python -m alpha_kd --backtest` runs without error.
- [ ] `alpha_kd/backtest_telemetry.py` ≤ 70 lines.
- [ ] No modifications to `Quantreo/Backtest.py`.
- [ ] Narrative report exists at `docs/reports/P2_backtest_telemetry_report.md`.

## Out of Scope (P3)

- Live data fetcher (Yahoo Finance / Upstox)
- Regime-aware strategy variant (`RsiSmaRegime`)
- Dashboard / UI
- Refactoring legacy `Quantreo/` modules
- Removing launcher scripts

---

*Plan authored by Hermes using writing-plans skill. Do not modify this file — append verification notes below if needed.*
