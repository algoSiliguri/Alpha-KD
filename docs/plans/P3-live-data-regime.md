# P3 Live Data + Regime-Aware Strategy Implementation Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make `python -m alpha_kd --backtest` fetch real historical data from Yahoo Finance, run it through a regime-aware RSI+SMA strategy, and emit telemetry.

**Architecture:**
- `alpha_kd/data_fetcher.py` — thin I/O module: fetches OHLCV via `yfinance`, caches to CSV, returns `pd.DataFrame`
- `alpha_kd/strategies/rsi_sma_regime.py` — extends `RsiSma` with HMM-based regime detection (hmmlearn already in deps)
- `alpha_kd/__main__.py` — wires fetch → strategy → `BacktestTelemetry` → summary print

**Tech Stack:** `yfinance` (new dep), `hmmlearn` (existing dep), `pandas`, `alpha_kd.backtest_telemetry`

---

## CI Gate Compliance

Before marking any task complete, verify:

- [ ] `pytest -q` passes with zero failures
- [ ] `ruff check alpha_kd/ tests/ --select E,W,F` reports zero errors
- [ ] Zero lines >88 characters (ruff E501)
- [ ] Zero wildcard imports (`from X import *`)
- [ ] `bandit -r alpha_kd/ -f json` reports zero HIGH-severity issues
- [ ] No new file exceeds 150 lines without ADR justification
- [ ] `yfinance` added to `pyproject.toml` dependencies

---

### Task 1: Add yfinance dependency

**Objective:** Add `yfinance` to `pyproject.toml` so CI installs it.

**Files:**
- Modify: `pyproject.toml:10-20`

**Step 1: Edit dependencies**

Add `"yfinance>=0.2.54",` to the `dependencies` list in `pyproject.toml`.

**Step 2: Verify file is valid TOML**

Run: `python3 -c "import tomllib; tomllib.load(open('pyproject.toml','rb'))"`
Expected: No output (success)

**Step 3: Commit**

```bash
git add pyproject.toml
git commit -m "deps: add yfinance for historical data fetching"
```

---

### Task 2: Create YahooFinanceFetcher

**Objective:** Build a thin I/O module that downloads OHLCV and caches to CSV.

**Files:**
- Create: `alpha_kd/data_fetcher.py`
- Test: `tests/test_data_fetcher.py`

**Step 1: Write failing test**

```python
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from alpha_kd.data_fetcher import YahooFinanceFetcher


class TestYahooFinanceFetcher:
    def test_fetch_returns_dataframe(self):
        fetcher = YahooFinanceFetcher()
        df = fetcher.fetch("AAPL", period="5d", interval="1d")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "close" in df.columns.str.lower()

    def test_cache_creates_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            fetcher = YahooFinanceFetcher(cache_dir=cache_dir)
            df = fetcher.fetch("AAPL", period="5d", interval="1d")
            cache_file = cache_dir / "AAPL_1d_5d.csv"
            assert cache_file.exists()
            df2 = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            assert len(df2) == len(df)
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_data_fetcher.py -v`
Expected: FAIL — `YahooFinanceFetcher not defined`

**Step 3: Write minimal implementation**

Create `alpha_kd/data_fetcher.py`:

```python
"""Thin I/O: fetch OHLCV from Yahoo Finance, cache to CSV."""
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from alpha_kd.config import DATA_DIR


class YahooFinanceFetcher:
    """Download historical bars from Yahoo Finance with local CSV cache."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or DATA_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1h",
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame, using cache if available."""
        cache_file = self.cache_dir / f"{symbol}_{interval}_{period}.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        df.columns = df.columns.str.lower().str.replace(" ", "_")
        df.to_csv(cache_file)
        return df
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_data_fetcher.py -v`
Expected: PASS (requires network; may be slow)

**Step 5: Commit**

```bash
git add alpha_kd/data_fetcher.py tests/test_data_fetcher.py
git commit -m "feat: add YahooFinanceFetcher with CSV cache"
```

---

### Task 3: Create RsiSmaRegime strategy

**Objective:** Extend `RsiSma` with HMM regime detection, adding regime label to state.

**Files:**
- Create: `alpha_kd/strategies/rsi_sma_regime.py`
- Test: `tests/test_rsi_sma_regime.py`

**Step 1: Write failing test**

```python
import numpy as np
import pandas as pd
import pytest

from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime


@pytest.fixture
def sample_df():
    dates = pd.date_range("2023-01-01", periods=100, freq="h")
    rng = np.random.default_rng(42)
    close = 100 + rng.standard_normal(100).cumsum()
    df = pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close},
        index=dates,
    )
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


def test_regime_state_key(sample_df, params):
    strategy = RsiSmaRegime(sample_df, params)
    state = strategy.get_state()
    assert "regime" in state
    assert state["regime"] in ("bull", "bear", "sideways", "unknown")
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_rsi_sma_regime.py -v`
Expected: FAIL — `RsiSmaRegime not defined`

**Step 3: Write minimal implementation**

Create `alpha_kd/strategies/rsi_sma_regime.py`:

```python
"""RSI+SMA strategy with HMM regime detection."""
from typing import Optional, Tuple

import pandas as pd
from hmmlearn.hmm import GaussianHMM

from alpha_kd.strategies.rsi_sma import RsiSma


class RsiSmaRegime(RsiSma):
    """Extends RsiSma with a 3-state HMM regime label."""

    def __init__(self, data: pd.DataFrame, parameters: dict):
        super().__init__(data, parameters)
        self.regime_label: str = "unknown"
        self._fit_regime()

    def _fit_regime(self) -> None:
        """Fit 3-state HMM on log-returns and label last bar."""
        returns = self.data["close"].pct_change().dropna().values.reshape(-1, 1)
        if len(returns) < 30:
            self.regime_label = "unknown"
            return
        try:
            model = GaussianHMM(
                n_components=3,
                covariance_type="diag",
                n_iter=100,
                random_state=42,
            )
            model.fit(returns)
            means = model.means_.flatten()
            # Sort regimes by mean return: bear < sideways < bull
            order = means.argsort()
            last_state = model.predict(returns)[-1]
            label_map = {order[0]: "bear", order[1]: "sideways", order[2]: "bull"}
            self.regime_label = label_map.get(last_state, "unknown")
        except Exception:
            self.regime_label = "unknown"

    def get_state(self) -> dict:
        state = super().get_state()
        state["regime"] = self.regime_label
        return state
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_rsi_sma_regime.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add alpha_kd/strategies/rsi_sma_regime.py tests/test_rsi_sma_regime.py
git commit -m "feat: add RsiSmaRegime with HMM regime detection"
```

---

### Task 4: Wire CLI --backtest

**Objective:** Make `python -m alpha_kd --backtest` fetch data, run strategy, and emit telemetry.

**Files:**
- Modify: `alpha_kd/__main__.py`
- Test: update `tests/test_backtest_telemetry.py` if needed

**Step 1: Write failing test**

Add to `tests/test_main.py` (or create it):

```python
import subprocess
import sys


def test_cli_backtest_flag_runs():
    result = subprocess.run(
        [sys.executable, "-m", "alpha_kd", "--backtest"],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0
    assert "bars" in result.stdout.lower() or "telemetry" in result.stdout.lower()
```

**Step 2: Run test to verify failure**

Run: `pytest tests/test_main.py -v`
Expected: FAIL — output does not contain "bars"

**Step 3: Write minimal implementation**

Modify `alpha_kd/__main__.py`:

Replace the `--backtest` stub with:

```python
    if args.backtest:
        from alpha_kd.backtest_telemetry import BacktestTelemetry
        from alpha_kd.data_fetcher import YahooFinanceFetcher
        from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime

        symbol = "AAPL"
        fetcher = YahooFinanceFetcher()
        df = fetcher.fetch(symbol, period="5d", interval="1h")
        params = {
            "fast_sma": 10,
            "slow_sma": 20,
            "rsi": 14,
            "tp": 0.01,
            "sl": -0.01,
            "cost": 0.0001,
            "leverage": 1,
        }
        bt = BacktestTelemetry(
            df,
            RsiSmaRegime,
            params,
            telemetry_path=args.telemetry_path,
        )
        bt.run()
        records = bt.buffer.tail(1)
        print(f"Backtest complete: {len(df)} bars")
        if records:
            print(f"Last state: {records[0]}")
```

**Step 4: Run test to verify pass**

Run: `pytest tests/test_main.py -v`
Expected: PASS (requires network)

**Step 5: Commit**

```bash
git add alpha_kd/__main__.py tests/test_main.py
git commit -m "feat: wire --backtest CLI to fetch + run backtest"
```

---

### Task 5: Narrative report

**Objective:** Write a novice-readable report explaining what P3 added and how to verify it.

**Files:**
- Create: `docs/reports/P3_live_data_regime_report.md`

**Content outline:**
1. **What P3 Added** — yfinance fetcher, CSV cache, HMM regime detection, wired CLI
2. **How to Verify** — commands for import check, running backtest, reading telemetry, lint
3. **Architecture** — ASCII diagram showing fetch → strategy → backtest → telemetry
4. **What Comes Next (P4)** — Dashboard, paper trading, multi-symbol support

**Step 1: Write report**

**Step 2: Commit**

```bash
git add docs/reports/P3_live_data_regime_report.md
git commit -m "docs: add P3 narrative report"
```

---

## Success Criteria

- [ ] `pytest -q` passes (all tests including new ones)
- [ ] `python -m alpha_kd --backtest` fetches AAPL data and prints bar count
- [ ] `ruff check alpha_kd/ tests/ --select E,W,F` passes
- [ ] Zero lines >88 chars
- [ ] Zero import *
- [ ] yfinance in pyproject.toml dependencies
