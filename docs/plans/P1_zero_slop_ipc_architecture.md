# P1: Zero-Slop IPC Architecture & Telemetry Pipeline

**Epic Summary:** Restructure Alpha-KD execution and telemetry to use zero-allocation `ctypes` memory-mapped ring buffers and strictly isolated IPC command ingestion, eradicating all global state pollution.

## Context
The legacy system suffers from severe coupling, state leakage (e.g., `MetricsUtility`), and blocking synchronous backtest loops. To feed a real-time, high-density UI without DOM degradation or execution delays, we must migrate to a zero-copy Single-Writer Multi-Reader (SWMR) telemetry pipeline and a double-buffered shared-memory state snapshot. The `ExecutionEngine` hot path must remain 100% allocation-free and non-blocking.

## Execution Checklist
- [ ] **Task 1: Define CTypes Schemas**
  - Implement `TelemetryHeader` (timestamp, strategy_id, status_flag, price, size, pnl, capital, payload_length).
  - Implement `DoubleBufferedSnapshot` containing `StrategySnapshot` arrays.
  - Location: `alpha_kd/telemetry/ipc_schemas.py`
  - Verification: `pytest tests/test_ipc_schemas.py` confirms `ctypes.sizeof` matches expected byte alignments perfectly.

- [ ] **Task 2: Implement Execution Engine Skeleton**
  - Create `ExecutionEngine` class initialized with `mmap` instances and `os.pipe` FD.
  - Implement non-blocking `poll_ipc_commands` using `os.read(fd, 4096)` catching `EAGAIN`.
  - Location: `alpha_kd/execution/engine.py`

- [ ] **Task 3: Refactor Backtest Monolith**
  - Strip `MetricsUtility` from `Quantreo/Backtest.py`.
  - Replace monolithic `for` loop with instantiation of `ExecutionEngine.run_loop()`.
  - Wrap historical dataframe generator as the `data_feed`.
  - Location: `Quantreo/Backtest.py`

- [ ] **Task 4: Update Strategies to ABC**
  - Create `BaseStrategy` with `__init__` and `on_tick(tick)`.
  - Migrate `CciStrategy.py` to inherit from `BaseStrategy`, returning `(Signal, payload_bytes)`.
  - Location: `alpha_kd/strategies/base.py`, `Strategies/CciStrategy.py`

## Success Criteria
1. The execution loop runs without any new object allocations inside the hot loop.
2. Telemetry is serialized via `ctypes` directly into the `mmap` buffer.
3. The UI can read the atomic double-buffered snapshot at any time without locking the engine.
4. IPC commands (e.g., Pause) are successfully ingested via a non-blocking pipe read.

## Narrative Report
*(To be completed by Claude Code upon task execution)*

---

### Appendix: Architectural Prototypes

#### 1. Zero-Allocation Telemetry Framing (ctypes)
```python
import ctypes

class TelemetryHeader(ctypes.Structure):
    _pack_ = 1  
    _fields_ = [
        ("timestamp_ns", ctypes.c_int64),
        ("strategy_id", ctypes.c_uint32),
        ("status_flag", ctypes.c_uint8),
        ("current_price", ctypes.c_float),
        ("position_size", ctypes.c_float),
        ("unrealized_pnl", ctypes.c_float),
        ("realized_pnl", ctypes.c_float),
        ("allocated_capital", ctypes.c_float),
        ("payload_length", ctypes.c_uint16),
    ]

class StrategySnapshot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("sequence_id", ctypes.c_uint64),
        ("is_active", ctypes.c_bool),
        ("unrealized_pnl", ctypes.c_float),
        ("allocated_capital", ctypes.c_float),
    ]

class DoubleBufferedSnapshot(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("active_index", ctypes.c_uint8),
        ("buffers", StrategySnapshot * 2)
    ]
```

#### 2. The Execution Loop Prototype (Non-Blocking IPC)
```python
import os
import errno
import ctypes
import mmap

class ExecutionEngine:
    def __init__(self, strategies, data_feed, ipc_pipe_fd: int, ring_mmap: mmap.mmap, snap_mmap: mmap.mmap):
        self.strategies = strategies
        self.data_feed = data_feed
        self.ipc_pipe_fd = ipc_pipe_fd
        self.ring_mmap = ring_mmap
        self.ring_offset = 0
        self.ring_size = len(ring_mmap)
        self.snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap_mmap)
        self.tick_sequence = 0

    def poll_ipc_commands(self) -> bytes:
        try:
            return os.read(self.ipc_pipe_fd, 4096)
        except OSError as e:
            if e.errno in (errno.EAGAIN, errno.EWOULDBLOCK):
                return b""
            raise

    def process_commands(self, raw_bytes: bytes):
        if not raw_bytes: return
        # Handle deterministic state mutations here
        pass

    def run_loop(self):
        header_size = ctypes.sizeof(TelemetryHeader)
        for tick in self.data_feed:
            self.tick_sequence += 1
            
            raw_cmds = self.poll_ipc_commands()
            if raw_cmds:
                self.process_commands(raw_cmds)

            for strategy in self.strategies:
                signal, var_payload = strategy.on_tick(tick)
                var_payload_len = len(var_payload) if var_payload else 0
                total_frame_size = header_size + var_payload_len

                if self.ring_offset + total_frame_size > self.ring_size:
                    self.ring_offset = 0 
                
                header = TelemetryHeader.from_buffer(self.ring_mmap, self.ring_offset)
                header.timestamp_ns = tick.timestamp_ns
                header.strategy_id = strategy.id
                header.payload_length = var_payload_len
                
                if var_payload_len > 0:
                    start_var = self.ring_offset + header_size
                    self.ring_mmap[start_var : start_var + var_payload_len] = var_payload
                
                self.ring_offset += total_frame_size
                
                inactive_idx = 1 - self.snapshot_mem.active_index
                target_buf = self.snapshot_mem.buffers[inactive_idx]
                target_buf.sequence_id = self.tick_sequence
                self.snapshot_mem.active_index = inactive_idx
```
