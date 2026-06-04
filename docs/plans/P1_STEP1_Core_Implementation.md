# P1 STEP 1: Core Implementation (Zero-Slop Telemetry & Strategy Base)

**Epic Summary:** Lock down the definitive zero-allocation, lock-free `ctypes` primitives and strategy boundaries in the codebase to enable native UI rendering and zero-latency execution.

## Context
The architectural rulings have been made. We are utilizing a pure-Python Sequence Lock (Seqlock), true zero-allocation memoryviews for variable strategy telemetry, Native Local UI via shared `mmap`, and native OS page cache delegation for flushing.
This plan defines the exact implementation specs for Claude Code.

## Execution Checklist

- [ ] **Task 1: Implement Telemetry Structures (`alpha_kd/telemetry/structures.py`)**
  - Create the exact `ctypes` structures defined below. Ensure `_pack_ = 1` is strictly enforced.
  - Verification: Run a Python script confirming `ctypes.sizeof(TelemetryHeader)` matches the byte expectations perfectly and instantiates without errors.

- [ ] **Task 2: Implement Seqlock Helper (`alpha_kd/telemetry/seqlock.py`)**
  - Implement the `SeqLock` class with `write_lock` and `read_retry` static methods exactly as defined.
  - Verification: Write a lightweight test proving the reader spins if the sequence is odd.

- [ ] **Task 3: Refactor BaseStrategy Contract (`alpha_kd/strategies/base.py`)**
  - Implement the `BaseStrategy` ABC with the strict `memoryview` signature to enforce the zero-allocation rule.
  - Verification: Ensure the module imports cleanly.

## Success Criteria
The structural foundational files exist in `alpha_kd/` exactly as specified, laying the absolute groundwork for the Execution Engine. No third-party packages or dynamic heap allocations are smuggled into the hot path definitions.

## Narrative Report
*(To be completed by Claude Code upon task execution)*

---

## CLAUDE CODE IMPLEMENTATION SPECS

### 1. `alpha_kd/telemetry/structures.py`
```python
import ctypes

class TelemetryHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = [
        ("seqlock", ctypes.c_uint64),        # Pure Python Seqlock
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
        ("seqlock", ctypes.c_uint64),        # Global seqlock for snapshot mutation
        ("active_index", ctypes.c_uint8),
        ("buffers", StrategySnapshot * 2)
    ]
```

### 2. `alpha_kd/telemetry/seqlock.py`
```python
import ctypes
import contextlib
from typing import Callable, Any

class SeqLock:
    """Helper for reading/writing pure Python Seqlocks."""
    
    @staticmethod
    @contextlib.contextmanager
    def write_lock(lock_ref: ctypes.c_uint64):
        """Context manager for the writer. Increments to odd, yields, increments to even."""
        lock_ref.value += 1  # Odd = writing in progress
        try:
            yield
        finally:
            lock_ref.value += 1  # Even = writing complete

    @staticmethod
    def read_retry(lock_ref: ctypes.c_uint64, read_func: Callable[[], Any]) -> Any:
        """
        Executes read_func and retries if the seqlock is odd (writing in progress) 
        or if it changed during the read.
        """
        while True:
            seq1 = lock_ref.value
            if seq1 % 2 != 0:
                continue # Spin if currently writing
            
            result = read_func()
            
            seq2 = lock_ref.value
            if seq1 == seq2:
                return result
```

### 3. `alpha_kd/strategies/base.py`
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseStrategy(ABC):
    """
    Pure state machine. Zero global state. No allocations on the hot path.
    """
    def __init__(self, strategy_id: int, parameters: Dict[str, Any]):
        self.id = strategy_id
        self.parameters = parameters
        self.status = 0
        self.unrealized_pnl = 0.0

    @abstractmethod
    def on_tick(self, tick: dict, current_state: dict, payload_buffer: memoryview) -> int:
        """
        Calculates signal and metrics purely from inputs.
        Must write directly to the pre-allocated `payload_buffer` memoryview.
        Must return the exact `payload_length` written.
        """
        pass
```
