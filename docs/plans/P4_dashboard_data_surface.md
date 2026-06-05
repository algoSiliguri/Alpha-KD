# Phase 4 Plan: Dashboard Data Surface & Observability Plane

## 1. Current Reality Summary

An audit of the Alpha-KD repository reveals that the codebase currently runs on **two completely independent and disconnected execution architectures** sharing no common strategy execution abstraction or data format:

1. **Legacy Bar-Level Research Path**:
   - **Interface**: Legacy `Strategy` ABC in [base.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/strategies/base.py) (uses `get_entry_signal()`, `get_exit_signal()`, `get_features()` and operates on `pandas.DataFrame`).
   - **Concrete Strategies**: `RsiSma` ([rsi_sma.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/strategies/rsi_sma.py)) and HMM-based `RsiSmaRegime` ([rsi_sma_regime.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/strategies/rsi_sma_regime.py)).
   - **Runner**: `BacktestTelemetry` in [backtest_telemetry.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/backtest_telemetry.py) (replays pandas bars one-by-one).
   - **Output**: Writes JSON lines directly to `telemetry.jsonl` via `TelemetryBuffer` ([telemetry/__init__.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/telemetry/__init__.py)).
   - **Status**: Research-only. Does not accumulate PnL or track actual capital.

2. **Zero-Allocation Tick-Level Streaming Path**:
   - **Interface**: `BaseStrategy` ABC in [base.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/strategies/base.py) (uses `on_tick()` with zero-allocation `memoryview` layout).
   - **Concrete Strategies**: `CciStrategy` ([cci_strategy.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/strategies/cci_strategy.py)) (`Stub in current codebase`).
   - **Runner**: `ExecutionEngine` ([engine.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/execution/engine.py)) (replays tick streams from compiled binary `.bin` files mapped with zero-copy `HistoricalFeed` mmap).
   - **Output**: Lock-free, zero-allocation binary `TelemetryHeader` updates pushed to a shared memory ring buffer (`ring_{session_id}`) and `DoubleBufferedSnapshot` (`snap_{session_id}`) synced via a custom `SeqLock` ([seqlock.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/telemetry/seqlock.py)).
   - **API/UI Connection**: FastAPI backend ([backend.py](file:///Users/koustavdas/Documents/GitHub/Alpha-KD/src/alpha_kd/ui/backend.py)) maps the shared memory segments, exposes `/api/telemetry/snapshot`, and streams binary bytes over WebSocket `/api/telemetry/ws` to a vanilla JS frontend using `uPlot` and `ArrayBuffer` decoding.
   - **Status**: Infrastructure-only. The strategy is a stub, and no trading signals are generated.

---

## 2. Accepted Product Decision

Milestone 1 will not attempt to force these two architectures into a unified execution or object model. Doing so would compromise either the convenience of historical research or the strict zero-allocation performance constraints of the tick-level engine.

Instead, the dashboard will honestly expose this duality via **two distinct dashboard modes**:

1. **Backtest Analysis Mode (Legacy Research Path)**:
   - **Purpose**: Allow research evaluation of strategies run via the bar-level path.
   - **Target UI Elements**: A strategy selector, a reconstructed equity curve chart, a regime color-band overlay, a reconstructed trade log, and computed performance/risk metrics.
   - **Data Source**: Reconstructed on-demand by backend endpoints reading `telemetry.jsonl` or running legacy backtests.

2. **Live Stream Mode (Zero-Alloc Streaming Path)**:
   - **Purpose**: Observe real-time streaming infrastructure, memory structures, and engine execution state.
   - **Target UI Elements**: Real-time price chart, allocated capital tracking, current position size, unrealized PnL, infrastructure ticks, and a system health indicator.
   - **Data Source**: Shared memory binary frames pushed via WebSocket.
   - **Warning**: A prominent notice must state that the active strategy (`CciStrategy`) is a stub.

---

## 3. Decision Record for the Five Open Questions

- **Q1: P4 Plan Required?**
  - **Decision**: Yes. Create this formal plan first. Do not write or modify implementation code.

- **Q2: Which execution path is primary?**
  - **Decision**: Neither is globally primary. The dashboard will use two separate modes (Option B) to honestly reflect their different purposes, capabilities, and data contracts.

- **Q3: Build forward-test now?**
  - **Decision**: No. Real forward-testing, broker integration, and live telemetry tracking are deferred (`Future option, not current implementation`). For Milestone 1, drift detection is unavailable, and no fake or simulated curves will be presented.

- **Q4: Persistence model?**
  - **Decision**: Start with standard JSONL (for legacy telemetry history) and static JSON exports. SQLite integration for database comparison is deferred (`Future option, not current implementation`).

- **Q5: Regime system?**
  - **Decision**: Surface only the HMM regime classification output (`bull`, `bear`, `sideways`, `unknown`) from `RsiSmaRegime` runs. The cooperative `RegimeMixin` is marked as unused (`Future option, not current implementation`). No KAIROS branding or transition matrices will be surfaced since they do not exist (`Not found in current codebase`).

---

## 4. Milestone 1 Backend Data-Surface Scope

Milestone 1 will define three new planned REST API endpoints to expose legacy backtest details to the frontend. These endpoints are currently `Not found in current codebase` and are target endpoints for future implementation:

1. **`GET /api/strategies`**: Returns a registry of all strategies available across both execution paths.
2. **`GET /api/backtest/{strategy_id}`**: Runs a legacy backtest on-demand for a given symbol/timeframe, reconstructs its equity curve and metrics, and returns the computed dataset.
3. **`GET /api/telemetry/history`**: Returns the list of raw historical bar snapshots captured inside `telemetry.jsonl`.

---

## 5. Target Files and Excluded Files

### Likely Future Implementation Targets (`Future option, not current implementation`):
- `src/alpha_kd/ui/backend.py` (Adding the new endpoints)
- `src/alpha_kd/metrics.py` (New module to handle metrics calculation, drawdown, and trade reconstruction from raw telemetry)
- `tests/test_metrics.py` (Unit tests verifying calculations)
- `tests/test_web_backend.py` (Integration tests verifying endpoint responses)

### Must Not Be Touched:
- Any files under `src/alpha_kd/ui/frontend/` (No UI changes)
- Any files under `src/alpha_kd/strategies/` (No base class refactoring, no strategy modifications)
- Any files under `src/alpha_kd/execution/` (No execution engine changes, no binary datafeed edits)
- Any files under `src/alpha_kd/telemetry/` (No shared memory changes, no structure/seqlock modifications)
- Any broker or infrastructure scripts

---

## 6. API Schema Drafts

These schema definitions outline the data contracts to be implemented by the backend.

### 1. `GET /api/strategies`
Returns metadata about available strategies.

```json
{
  "strategies": [
    {
      "strategy_id": "rsi_sma",
      "strategy_name": "RsiSma",
      "path": "legacy",
      "status": "research_only",
      "parameters": {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1
      },
      "regime_aware": false,
      "has_real_data": true
    },
    {
      "strategy_id": "rsi_sma_regime",
      "strategy_name": "RsiSmaRegime",
      "path": "legacy",
      "status": "research_only",
      "parameters": {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1
      },
      "regime_aware": true,
      "has_real_data": true
    },
    {
      "strategy_id": "cci",
      "strategy_name": "CciStrategy",
      "path": "zero_alloc",
      "status": "stub",
      "parameters": {
        "cci_period": 20,
        "atr_period": 20
      },
      "regime_aware": false,
      "has_real_data": false
    }
  ]
}
```

### 2. `GET /api/backtest/{strategy_id}`
Returns on-demand legacy backtest results and computed stats.

```json
{
  "strategy_id": "rsi_sma_regime",
  "symbol": "string",
  "period": "string",
  "interval": "string",
  "bars_processed": "integer",
  "equity_curve": ["list of floats"],
  "cumulative_returns": ["list of floats"],
  "per_bar": [
    {
      "bar_time": "string (ISO 8601 or offset timestamp)",
      "side": "string ('buy' | 'sell' | 'flat')",
      "entry_price": "float or null",
      "unrealized_pnl": "float or null",
      "signal": "integer (-1 | 0 | 1)",
      "entry_signal": "integer (-1 | 0 | 1)",
      "exit_return": "float",
      "regime": "string ('bull' | 'bear' | 'sideways' | 'unknown')"
    }
  ],
  "trades": [
    {
      "entry_time": "string (ISO 8601)",
      "exit_time": "string (ISO 8601)",
      "side": "string ('buy' | 'sell')",
      "entry_price": "float",
      "exit_price": "float (computable but not currently implemented)",
      "exit_return": "float",
      "regime_at_entry": "string ('bull' | 'bear' | 'sideways' | 'unknown')"
    }
  ],
  "metrics": {
    "total_return": "float",
    "sharpe_ratio": "float or null",
    "max_drawdown": "float",
    "drawdown_duration_bars": "integer",
    "num_trades": "integer",
    "win_rate": "float",
    "profit_factor": "float",
    "avg_trade_duration_bars": "float",
    "sortino_ratio": "float or null"
  },
  "regime_timeline": ["list of strings ('bull' | 'bear' | 'sideways' | 'unknown')"],
  "forward_test": null
}
```

### 3. `GET /api/telemetry/history`
Exposes raw telemetry JSONL logs.

```json
{
  "records": [
    {
      "side": "string",
      "entry_price": "float or null",
      "unrealized_pnl": "float or null",
      "signal": "integer",
      "timestamp": "string",
      "regime": "string",
      "bar_time": "string",
      "entry_signal": "integer",
      "exit_return": "float"
    }
  ],
  "total_records": "integer"
}
```

---

## 7. Metrics Classification

Metrics to be surfaced are classified into three precise readiness states:

### 1. Already Present (`Exists in current codebase`)
- **`per-bar signal`**: `signal` column or dict key.
- **`side`**: `side` state value (`flat`, `buy`, `sell`).
- **`entry price`**: `entry_price` or open price when entry occurs.
- **`unrealized PnL`**: Computed per-bar in strategy based on close vs entry.
- **`exit_return`**: Exit return percentage calculated at trade exit bar.
- **`regime label`**: `regime_label` determined from the HMM fit.

### 2. Computable But Not Currently Implemented (`Computable from existing telemetry, but not currently implemented`)
- **`equity_curve`**: Must be accumulated by applying sequential bar returns (starting at a base capital like `100,000` and compounding/accumulating using trade returns).
- **`cumulative return`**: Cumulative sum or product of returns series.
- **`max drawdown`**: Calculated by tracking high-water marks of the reconstructed equity curve and taking the max drop peak-to-trough.
- **`drawdown duration`**: The maximum number of consecutive bars spent below the trailing high-water mark.
- **`win rate`**: Ratio of trades where `exit_return > 0` over total trades.
- **`profit_factor`**: Ratio of `sum(gross profits) / sum(gross losses)`.
- **`simple trade reconstruction`**: Combining entry and exit event timestamps and prices from raw telemetry to build a trade sequence.
- **`Sortino / Sharpe ratios`**: Calculated mathematically on returns series if data length permits.

### 3. Future-Only / Not Currently Supported (`Future option, not current implementation`)
- **`forward-test drift`**: `Not found in current codebase` (requires live execution / paper trading database baseline).
- **`live-vs-backtest comparison`**: `Not found in current codebase`.
- **`broker fills`**: No broker execution loop exists.
- **`realized live PnL`**: No live positions or live accounts.
- **`slippage analysis`**: No trading execution layer details captured.
- **`multi-strategy portfolio analytics`**: No portfolio grouping or covariance models exist.

---

## 8. Testing Criteria

Before any backend data implementation is marked complete, the following tests must be successfully implemented:

1. **Deterministic Metrics Verification**:
   - Write unit tests that pass a mock array of returns (e.g., static, known sequences of profits and losses) to verify that max drawdown, drawdown duration, Sharpe ratio, Sortino ratio, win rate, and profit factor are calculated with mathematical precision.
2. **Trade Reconstruction Validation**:
   - Test trade matching logic: verify that a sequence of bar signals correctly matches entries and exits into distinct, closed trade logs.
3. **Telemetry JSONL Parser Verification**:
   - Verify that the API parser handles corrupt, incomplete, or duplicated lines in `telemetry.jsonl` gracefully without raising server-side errors.
4. **API Endpoint Schema Conformance**:
   - Write integration tests verifying that `/api/strategies`, `/api/backtest/{strategy_id}`, and `/api/telemetry/history` return the exact JSON payload structures defined in Section 6.
5. **No Production Path Mocks**:
   - No mock market data or fake historical curves are permitted in the calculation paths.

---

## 9. Explicit Non-Goals

- **No UI implementation**: Do not write, modify, or bundle HTML, CSS, or JS code.
- **No fake data**: Do not create fake historical files or fake backtest curves.
- **No forward-test implementation**: Do not build paper-trading schedulers or real-time polling clients.
- **No broker integration**: Do not initialize MetaTrader5 or Upstox APIs in the server pathways.
- **No SQLite**: Do not create or migrations-manage database files for backtests.
- **No strategy refactoring**: Do not touch `BaseStrategy` or `Strategy` base interfaces, and do not modify existing logic.
- **No architecture merge**: Do not unify the zero-alloc execution paths with the pandas-based backtester.
- **No KAIROS branding**: Surfacing HMM regimes is allowed; inventing complex transition/probability matrices or naming them KAIROS is banned.
- **No modification of zero-alloc streaming path**: Leave `ExecutionEngine`, `HistoricalFeed`, and `structures.py` untouched.
- **No promotion of `CciStrategy`**: It must remain marked as a stub strategy.

---

## 10. Next Step After Plan

After this P4 plan is reviewed and accepted, the next implementation step should be a small backend-only change that computes dashboard-ready metrics from existing legacy telemetry without touching the zero-alloc streaming path.
