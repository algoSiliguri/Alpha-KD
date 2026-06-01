# P1 Phase Report: Package & Contract

**Date:** 2026-06-01
**Branch:** `feature/p1-package-contract`
**Status:** Complete — all 6 tasks done, 3/3 tests passing

---

## What We Found

The Alpha-KD codebase had 91 Python files with no package structure. There were 76 wildcard imports (`from X import *`), meaning any file could silently depend on any name without declaring it. The strategy logic for RSI+SMA existed only as a standalone class in `Strategies/LI_2023_02_RsiSma.py` with no shared interface — making it impossible to write generic backtesting or testing code that works across all strategies.

There were also hardcoded paths and broker credentials scattered across source files.

---

## What Was Done

### 1. `pyproject.toml` — package metadata
Declared `alpha-kd` as a proper Python package with all dependencies listed. This means `pip install -e .` works and all imports resolve cleanly.

### 2. `alpha_kd/config.py` — centralized config
All paths (DATA_DIR, MODELS_DIR) and trading defaults (BROKER_TYPE, DEFAULT_SYMBOL, DEFAULT_TIMEFRAME) now load from environment variables via `python-dotenv`. A `.env.example` file shows which keys are needed without storing any real values.

### 3. `alpha_kd/strategies/base.py` — Strategy ABC
Defined a `Strategy` abstract base class with three methods every strategy must implement:
- `get_features()` — compute indicators
- `get_entry_signal(time)` — return -1, 0, or 1
- `get_exit_signal(time)` — return P&L if position closes

This is the contract. Any strategy that doesn't implement all three will fail to instantiate.

### 4. `alpha_kd/strategies/rsi_sma.py` — RsiSma migrated
Rewrote `LI_2023_02_RsiSma.py` to implement the `Strategy` ABC. Same logic, zero behavior changes. No wildcard imports — `ta` functions are called directly.

### 5. `tests/test_strategies.py` — contract tests
Three pytest tests verify that:
- `RsiSma` can be constructed
- `get_entry_signal` returns a valid signal value (-1, 0, or 1)
- `get_exit_signal` returns a numeric return

All 3 pass in under 1 second.

---

## Key Insight

One strategy now lives in a testable package with explicit imports. This is a proof of concept: the pattern works. The contract (`Strategy` ABC + three methods) is the foundation that makes every future migration mechanical rather than creative.

---

## What Comes Next

- **P1.5:** Migrate the remaining 6 strategies (`LI_2023_02_*`) to the same `Strategy` ABC. Each migration is now a copy-adapt-test cycle.
- **P2:** Connect regime detection (`MarketDownRegimeAnalyzer`, HMM states) so strategies can switch behavior based on market regime.
- **P5 (later):** Refactor live trading execution to use the same `Strategy` interface.
