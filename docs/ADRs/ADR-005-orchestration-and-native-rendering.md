# ADR-005: Lifecycle Orchestration & Native Rendering

**Status:** Approved
**Context:** Eradicating zombie shared memory segments through deterministic startup/teardown rituals and ensuring the UI rendering pipeline honors the zero-allocation mandate via C-level memory bindings.

## 1. The Shared Memory Zombie Problem (The Orchestrator)
**Decision:** **The Idempotent Clean-Slate Ritual & Parent Orchestration.**

*   **Structure:** We introduce an absolute master orchestrator script (`run_alpha.py`). This is the only entry point. It spawns the `ExecutionEngine` and `NativeUI` as strict OS subprocesses.
*   **The Ritual:** Before mapping any new memory or spinning up children, the Orchestrator executes a hard-coded purge. It iterates over all registered shared memory names (`/alpha_kd_ring_0`, `/alpha_kd_snap_0`). It aggressively attempts to attach and `.unlink()` them, swallowing `FileNotFoundError`. If physical backing files exist from a crashed run, they are zeroed out or deleted.
*   **Safe Teardown:** The Orchestrator traps `SIGINT`/`SIGTERM`. Upon receipt, it dispatches an `IPC_HALT` command down the Unix pipe to the Engine. The Engine completes its current tick, executes `mmap.flush()`, and safely returns `0`. The Orchestrator `join()`s both child processes, unlinks the memory segments one final time, and dies clean. No zombies.

## 2. The Native UI Zero-Allocation Render Loop
**Decision:** **Direct C-Array Binding via Dear PyGui.**

*   **Structure:** Dear PyGui (DPG) is built entirely in C++ and allows binding data to plots directly via contiguous memory arrays. We will strictly forbid standard Python loops that extract floats to feed the UI.
*   **The Ritual:** The Native UI maps the telemetry ring buffer into a strided `numpy.ndarray` backed directly by the `mmap` buffer (e.g., `np.ndarray(shape=(MAX_FRAMES,), dtype=TelemetryHeader_dtype, buffer=ring_mmap)`). 
*   **The Render Loop:** At 60Hz, the UI evaluates the Seqlock to find the current valid head index. To update the equity curve chart, the UI simply passes the sliced memory view (e.g., `mmap_array['allocated_capital'][0:head_index]`) directly into `dpg.set_value()`. Dear PyGui's C++ backend iterates over the raw contiguous memory pointer instantly. Zero Python `float` objects are instantiated. Zero GC spikes.
