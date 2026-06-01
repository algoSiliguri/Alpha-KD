# P1: Package & Contract — Execution Plan

> **Epic:** P1 Package & Contract  
> **Phase:** P1 (Foundation)  
> **Branch:** `feature/p1-package-contract`  
> **Agent:** Claude Code  
> **Estimated Time:** ~25 minutes  
> **Goal:** Prove the new package structure works by migrating ONE strategy to a unified `Strategy` ABC.

---

## Context

Alpha-KD currently has 91 Python files with no package structure, 76 wildcard imports, and strategy logic duplicated in two places. Before any agent can work on this codebase reliably, we need:

1. A Python package (`alpha_kd/`) with explicit imports
2. A unified `Strategy` base class that all strategies implement
3. A config layer that externalizes secrets and paths
4. A pytest suite that verifies the contract

This plan migrates **only `RsiSma`** as a proof-of-concept. The other 6 strategies follow in P1.5 once the contract is proven.

---

## Execution Checklist

### Task 1: Create `pyproject.toml`
**Objective:** Define the package metadata, dependencies, and entry points.

**Files:**
- Create: `pyproject.toml`

**Details:**
- Package name: `alpha-kd`
- Version: `0.1.0`
- Dependencies: `pandas`, `numpy`, `scikit-learn`, `matplotlib`, `ta`, `hmmlearn`, `statsmodels`, `requests`, `python-dotenv`
- Optional dev deps: `pytest`, `pytest-cov`
- Python requirement: `>=3.9`

**Verification:**
```bash
python -c "import tomllib; f=open('pyproject.toml','rb'); tomllib.load(f); print('OK')"
```

**Commit:** `git add pyproject.toml && git commit -m "build: add pyproject.toml with package metadata"`

---

### Task 2: Create `alpha_kd/config.py`
**Objective:** Externalize all constants, paths, and secrets. Zero hardcoded values in source.

**Files:**
- Create: `alpha_kd/__init__.py`
- Create: `alpha_kd/config.py`
- Create: `.env.example`

**Details:**
- `config.py` loads env vars via `python-dotenv`
- Exposes: `DATA_DIR`, `MODELS_DIR`, `BROKER_TYPE` (mt5/upstox), `DEFAULT_SYMBOL`, `DEFAULT_TIMEFRAME`
- `.env.example` has blank placeholders for all secrets
- No secrets in `.env.example` — only keys

**Verification:**
```bash
python -c "from alpha_kd.config import DATA_DIR; print(DATA_DIR)"
```

**Commit:** `git add alpha_kd/__init__.py alpha_kd/config.py .env.example && git commit -m "feat: add config layer with env var loading"`

---

### Task 3: Create `alpha_kd/strategies/base.py`
**Objective:** Define the unified `Strategy` abstract base class that all strategies must implement.

**Files:**
- Create: `alpha_kd/strategies/__init__.py`
- Create: `alpha_kd/strategies/base.py`

**Details:**
```python
from abc import ABC, abstractmethod
from typing import Tuple, Optional
import pandas as pd

class Strategy(ABC):
    """Unified interface for all Alpha-KD trading strategies."""

    def __init__(self, data: pd.DataFrame, parameters: dict):
        self.data = data
        self.parameters = parameters
        self.get_features()
        self.start_date_backtest = self.data.index[0]
        self.buy = False
        self.sell = False
        self.open_buy_price: Optional[float] = None
        self.open_sell_price: Optional[float] = None
        self.entry_time: Optional[pd.Timestamp] = None
        self.exit_time: Optional[pd.Timestamp] = None

    @abstractmethod
    def get_features(self) -> None:
        """Compute technical indicators and signal columns on self.data."""
        ...

    @abstractmethod
    def get_entry_signal(self, time: pd.Timestamp) -> Tuple[int, Optional[pd.Timestamp]]:
        """Return entry signal (-1, 0, 1) and entry time."""
        ...

    @abstractmethod
    def get_exit_signal(self, time: pd.Timestamp) -> Tuple[float, Optional[pd.Timestamp]]:
        """Return position return and exit time if closing."""
        ...
```

**Verification:**
```bash
python -c "from alpha_kd.strategies.base import Strategy; print('Strategy ABC loaded')"
```

**Commit:** `git add alpha_kd/strategies/__init__.py alpha_kd/strategies/base.py && git commit -m "feat: add Strategy ABC with unified interface"`

---

### Task 4: Create `alpha_kd/strategies/rsi_sma.py`
**Objective:** Migrate `RsiSma` from `Strategies/LI_2023_02_RsiSma.py` to implement the new `Strategy` ABC.

**Files:**
- Create: `alpha_kd/strategies/rsi_sma.py`

**Details:**
- Import `Strategy` from `alpha_kd.strategies.base`
- Import feature helpers from `alpha_kd.data.features` (create stub if needed)
- Implement `get_features()`, `get_entry_signal()`, `get_exit_signal()`
- Keep the exact same logic as the original — zero behavior changes
- No `import *`
- No `plt.show()`

**Verification:**
```bash
python -c "from alpha_kd.strategies.rsi_sma import RsiSma; print('RsiSma imported OK')"
```

**Commit:** `git add alpha_kd/strategies/rsi_sma.py && git commit -m "feat: migrate RsiSma to Strategy ABC"`

---

### Task 5: Create `tests/test_strategies.py`
**Objective:** Verify that `RsiSma` correctly implements the `Strategy` ABC.

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/test_strategies.py`

**Details:**
```python
import pytest
import pandas as pd
import numpy as np
from alpha_kd.strategies.rsi_sma import RsiSma

@pytest.fixture
def sample_data():
    dates = pd.date_range("2023-01-01", periods=200, freq="H")
    np.random.seed(42)
    data = pd.DataFrame({
        "open": 1.0 + np.random.randn(200).cumsum() * 0.01,
        "high": 1.0 + np.random.randn(200).cumsum() * 0.01 + 0.005,
        "low": 1.0 + np.random.randn(200).cumsum() * 0.01 - 0.005,
        "close": 1.0 + np.random.randn(200).cumsum() * 0.01,
    }, index=dates)
    data["high_time"] = data.index
    data["low_time"] = data.index
    return data

def test_rsi_sma_implements_strategy(sample_data):
    params = {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }
    strategy = RsiSma(sample_data, params)
    assert hasattr(strategy, "get_entry_signal")
    assert hasattr(strategy, "get_exit_signal")
    assert hasattr(strategy, "get_features")

def test_rsi_sma_entry_signal(sample_data):
    params = {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }
    strategy = RsiSma(sample_data, params)
    time = sample_data.index[50]
    signal, entry_time = strategy.get_entry_signal(time)
    assert signal in (-1, 0, 1)

def test_rsi_sma_exit_signal(sample_data):
    params = {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }
    strategy = RsiSma(sample_data, params)
    time = sample_data.index[50]
    ret, exit_time = strategy.get_exit_signal(time)
    assert isinstance(ret, (int, float))
```

**Verification:**
```bash
python -m pytest tests/test_strategies.py -v
```
Expected: 3 passed

**Commit:** `git add tests/__init__.py tests/test_strategies.py && git commit -m "test: add Strategy ABC contract tests for RsiSma"`

---

### Task 6: Write `docs/reports/P1_report.md`
**Objective:** Produce a novice-readable narrative report proving the contract works.

**Files:**
- Create: `docs/reports/P1_report.md`

**Details:**
- Explain what was analyzed (the old codebase structure)
- Explain what was done (created package, Strategy ABC, migrated RsiSma)
- Key insight: "One strategy now lives in a testable package with explicit imports"
- What to do next: "Migrate remaining 6 strategies in P1.5, then connect regime detection in P2"

**Verification:**
```bash
ls docs/reports/P1_report.md
```

**Commit:** `git add docs/reports/P1_report.md && git commit -m "docs: add P1 narrative report"`

---

## Success Criteria

1. `python -m pytest tests/test_strategies.py` passes with 3/3 tests
2. `python -c "from alpha_kd.strategies.rsi_sma import RsiSma; print('OK')"` works without errors
3. No `import *` in any new file under `alpha_kd/` or `tests/`
4. `.env.example` exists with blank placeholders
5. `docs/reports/P1_report.md` exists and is readable by a non-technical user

---

## Narrative Report

*Pending execution by Claude Code...*

---

## Notes

- **Do NOT migrate other strategies yet.** P1 is proof-of-concept only.
- **Do NOT refactor Quantreo yet.** That is P1.5 after the contract is proven.
- **Do NOT touch live trading code.** That is P5.
- If a task fails, stop and report. Do not proceed to the next task.
