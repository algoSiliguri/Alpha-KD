# ADR-004: Zero-Allocation Inference & Lapping Safeguards

**Status:** Approved
**Context:** Finalizing the last 2% of zero-slop execution constraints: eradicating hidden machine learning allocations, mitigating SWMR ring buffer lapping, and enforcing strict in-place NumPy mutation.

## 1. The Machine Learning Allocation Trap (Inference Runtime)
**Decision:** We will leverage **ONNX Runtime (ORT) with explicit I/O Binding** for complex models, and **m2cgen (Model to Code)** for simple linear/tree models.

*   **The Interface Shape:** 
    Standard `joblib` scikit-learn pipelines allocate memory. We will mandate that all ML models be exported to ONNX. During `BaseStrategy.__init__`, the strategy will instantiate an `InferenceRuntime` and pre-allocate two continuous memory blocks: an `input_tensor_mview` and an `output_tensor_mview`.
*   **The Execution Footprint:** 
    Instead of calling `.predict()`, `on_tick` will write its standardized features directly into `input_tensor_mview`. We will trigger `session.run_with_iobinding()`. ORT will read the inputs and write the predictions directly into `output_tensor_mview` via a pure C-level memory copy, guaranteeing exactly zero Python object allocations or garbage collection triggers during inference.

## 2. The "Lapping" Race Condition
**Decision:** **Seqlock Discontinuity Detection & Pointer Reset.**

*   **The Mechanic:** 
    A multi-gigabyte backtest will outpace a 60fps UI reader. The `TelemetryHeader` contains our `seqlock` (a strictly monotonic `uint64`). The Native UI reader tracks `last_read_seqlock`. 
*   **The Guardrail:** 
    When the UI reader begins to read a frame, it checks the frame's `seqlock`. If `current_seqlock > last_read_seqlock + 2` (or whatever the expected stride is), it mathematically proves the writer has lapped the reader and overwritten the physical memory. 
*   **The Resolution:** 
    Upon detecting a discontinuity, the UI reader aborts the current read, queries the `DoubleBufferedSnapshot` to locate the writer's exact current byte offset (the "Head"), fast-forwards its pointer to the Head, and resumes reading the bleeding edge. Missed visual frames are silently dropped without crashing or parsing corrupted mid-overwrite structs.

## 3. NumPy Circular Buffers vs Ctypes Arrays
**Decision:** **Mandatory `out=` Parameter Contracts.**

*   **The Mechanic:** 
    Any mathematical calculation performed inside the `alpha_kd` execution layer must use NumPy's in-place operations. Computations like Moving Averages or standard deviations must be written as `np.mean(buffer, axis=0, out=target_view)`. Slicing operations will only be permitted if they return `view()` objects, completely banning implicit copies.
