# ADR-003: Zero-Slop Refactoring Bottlenecks

**Status:** Approved
**Context:** The architecture demands true zero-allocation execution and strict isolation. The legacy codebase contains monolithic strategies, duplicated ingestion loops, and naive buffer handling. We must define the exact teardown and restructuring blueprint before laying new engine code.

## Blueprint 1: Dismantling the `CciStrategy.py` Monolith
The legacy `CciStrategy` violates single-responsibility by managing global capital and running dataframe-level feature engineering during tick evaluation.

*   **Feature Engineering (The Zero-Allocation Fix):** 
    We completely ban `pandas` from the hot path. For offline backtesting, `DataFeed` will pre-compute features (CCI, ATR) in a vectorized manner *before* the tick loop starts, yielding them inside the `TickData` struct. For live execution where vectors don't exist, the strategy's `__init__` will allocate a fixed-size `numpy` array (e.g., `np.zeros(cci_period)`) acting as a circular buffer. `on_tick` will update the ring buffer index and compute the value inline without allocating a single new object.
*   **Position Sizing (The State Boundary Fix):**
    `CciStrategy` will never import or call `MetricsUtility`. Instead, `on_tick` will return a `Signal(target_exposure=1.0)` indicating "I want 100% of my allocated risk budget long." The isolated `ExecutionEngine` maintains the global state and translates that `1.0` exposure into an exact share count based on live margin/capital, executing the trade and updating the strategy's internal PnL variables inside the `StrategySnapshot`.

## Blueprint 2: Resolving the `LiveTradingSignal.py` Code Duplication
The legacy codebase maintains two parallel universes: `Backtest.py` and `LiveTradingSignal.py`, ensuring divergent behaviors.

*   **Unified `TickData` Interface:**
    We implement a strict `AbstractDataFeed` yielding `TickData` (a `ctypes.Structure`). 
    *   `HistoricalFeed` reads the CSV, pre-computes indicators, and yields `TickData` frames.
    *   `LiveFeed` listens to Upstox/MetaTrader WebSockets, instantly populates the exact same `TickData` struct, and yields.
    The `BaseStrategy` has absolutely no idea if it is running live or offline.
*   **ML Model Initialization:**
    Heavy I/O like `joblib.load()` is moved strictly into the `BaseStrategy.__init__()` method. The model weights are pinned into memory before the `run_loop` begins. The `on_tick` function only executes the inference pass against the incoming `TickData` array.

## Blueprint 3: Safe Ring Buffer Wraparound
In a lock-free SWMR ring buffer, partial frames at the end of the `mmap` segment will corrupt the native UI reader.

*   **The `FLAG_WRAPAROUND` Control Frame:**
    If the engine calculates that `current_offset + sizeof(TelemetryHeader) + payload_length` exceeds the total `mmap` boundary, it **aborts the write at that offset**.
*   **The Mechanic:**
    1.  The engine writes a terminal `TelemetryHeader` at the `current_offset` with `status_flag = 0xFF` (representing `FLAG_WRAPAROUND`) and `payload_length = 0`.
    2.  The engine resets its internal `current_offset` pointer to `0`.
    3.  The engine writes the actual new tick frame at offset `0`.
    4.  The Native UI reader, sweeping through the buffer, hits the `0xFF` flag, immediately discards the remaining trailing bytes, resets its read pointer to `0`, and seamlessly resumes reading the newest frames. No garbage memory is ever parsed.
