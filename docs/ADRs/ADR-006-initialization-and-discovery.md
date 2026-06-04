# ADR-006: Runtime Initialization & Strict Boundaries

**Status:** Approved
**Context:** Final lock-down of system initialization boundaries before physical scaffolding to prevent memory collisions, hot-loop ingestion allocations, and execution coupling.

## Blueprint 1: Runtime Instance Scoping (Environment Sandboxing)
**Decision:** **Orchestrator Session ID Injection via Environment Variables.**
*   `run_alpha.py` accepts a `--session-id` flag (defaulting to a deterministic hash if omitted).
*   This ID is used to dynamically construct all IPC pipe names and shared memory descriptors (e.g., `/alpha_kd_ring_SESSION_001`).
*   The Orchestrator securely injects this string into the `ExecutionEngine` and `NativeUI` child processes via `os.environ["ALPHA_SESSION_ID"]`. The children dynamically build their `mmap` endpoints using this variable, guaranteeing absolutely zero collision during parallel backtest sweeps or concurrent live deployment.

## Blueprint 2: Binary Memory Boundary for Data Ingestion
**Decision:** **Pre-Compiled `.bin` Maps (No CSV parsing in hot loops).**
*   **The Pipeline:** An offline utility script compiles standard CSV market data into a flat, packed `.bin` file where every row perfectly mirrors the byte alignment of the `TickData` C-struct.
*   **The Ingestion:** `HistoricalFeed` will natively map the `.bin` file into memory via `mmap`. Ticks are iterated using raw pointer arithmetic (`ctypes.cast`) or NumPy buffer views (`np.frombuffer(mmap, dtype=TickData_dtype)`). This guarantees zero string parsing, zero object instantiation, and direct cache-line loads.

## Blueprint 3: Stateless Strategy Discovery
**Decision:** **Module-Level Decoration & Dictionary Registry.**
*   **The Open/Closed Fix:** Strategies will be decorated with `@register_strategy("CciStrategy")`, which maps their class to a static dictionary in `alpha_kd/strategies/__init__.py`. 
*   **The Instantiation:** The `ExecutionEngine` reads a static `.yaml` configuration file before the hot loop starts. It performs an `O(1)` dictionary lookup `STRATEGY_REGISTRY[config.strategy_type]` to instantiate the correct class. No runtime reflection, no hardcoded engine imports.

---

### UI Configuration Transport Protocol
The Native UI process will receive its configuration strictly via **Direct Command-Line Arguments** passed from the master orchestrator. 

Attempting to read configuration dynamically from a shared memory segment introduces a chicken-and-egg vulnerability: the UI needs to know the exact session hash to map the correct memory segment in the first place. Passing `--session-id`, `--ui-layout`, and read-only flags via `sys.argv` is absolute, stateless, and resolves instantaneously before the UI memory allocator even boots.
