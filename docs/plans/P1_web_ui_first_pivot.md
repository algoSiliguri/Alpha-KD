# Phase 1/2: Package Refactor & Web UI First Pivot

**Epic Summary:** Refactor the Alpha-KD repository into a standard `src/` layout using `uv` packaging, enforce strict execution-path dependency isolation, and implement a high-performance, asynchronous Web UI telemetry platform.

---

## Context
The legacy repository structure suffers from loose dependency management and lacks proper namespace isolation. Moving the core execution domain into a standard `src/` layout with `uv` ensures deterministic builds. Crucially, runtime execution must remain free of heavy packages like `pandas` and `scikit-learn` (per ADR-003/004) to prevent heap allocations. Telemetry is streamed out-of-band to a lightweight Web UI, utilising `uPlot` for ultra-low latency, canvas-based rendering.

---

## Execution Checklist

### Task 1: Relocate Codebase to `src/` Layout
- Create a `src/` container directory at the project root.
- Move the `alpha_kd` module folder into `src/alpha_kd`.
- Verification: `ls src/alpha_kd` displays the module directories cleanly.

### Task 2: Configure `pyproject.toml` & Dependency Isolation
- Create/overwrite `pyproject.toml` using `hatchling` as the build backend.
- Set primary dependencies strictly to: `fastapi`, `uvicorn`, `websockets`, and `onnxruntime` (for zero-allocation inference).
- Place `pandas`, `scikit-learn`, `matplotlib`, and `yfinance` strictly in the `[dependency-groups]` / dev optional dependencies for offline research only.
- Configure packaging exclusion for `src/alpha_kd/ui/frontend/node_modules/` and frontend build artifacts.
- Create a `.python-version` file containing `3.10` or `3.11`.
- Delete the legacy `requirements.txt`.
- Verification: Run `uv sync` to build the isolated environment and verify `uv.lock` is generated.

### Task 3: Implement FastAPI Binary Streaming Backend
- Create `src/alpha_kd/ui/backend.py`.
- Implement a FastAPI app with a WebSocket endpoint `/api/telemetry/ws`.
- Connect directly to the existing shared-memory `mmap` ring buffer, evaluate the Seqlock natively via the `seqlock.py` primitives, and stream raw bytes without intermediate allocations.
- Implement an HTTP GET `/api/telemetry/snapshot` endpoint to return the current `DoubleBufferedSnapshot` structure for initial loads.
- Ensure the backend runs in a detached subprocess to prevent blocking the core engine.
- Verification: Run `pytest tests/test_web_backend.py` to confirm endpoint availability and binary payloads.

### Task 4: Scaffold Frontend with `uPlot`
- Initialize a Vite + React (or Vanilla JS) app inside `src/alpha_kd/ui/frontend/`.
- Configure `package.json` to include `uPlot` as the primary high-performance plotting dependency.
- Set up the main JS entrypoint to parse incoming WebSocket binary payloads natively via `DataView` and typed arrays.
- Verification: Run `cd src/alpha_kd/ui/frontend && npm run build` to verify the build processes without syntax or bundling errors.

### Task 5: Integration & End-to-End Test
- Launch backend server: `uv run python -m alpha_kd.ui.backend --session-id dev-test`.
- Write or run a mock strategy loop writer pushing binary ticks to the ring buffer.
- Connect the frontend dashboard and verify the uPlot chart updates smoothly at 60fps without lag.
- Verification: Perform a manual visual verification of the updating curves on `http://localhost:5173` or backend port.

### Task 6: Narrative Report
- Write `docs/reports/P1_web_ui_first_pivot_report.md` detailing the transition, dependencies, and performance benchmarks.
- Verification: File is populated with narrative results.

---

## Success Criteria
1. The repository runs inside an isolated, deterministic environment managed by `uv`.
2. Core runtime code imports only `fastapi`, `uvicorn`, `websockets`, `onnxruntime`, and Python standard libraries.
3. Telemetry flows from the execution engine to the browser over binary WebSockets with zero Python object allocations.
4. The client browser decodes the `ArrayBuffer` directly using Typed Arrays and feeds `uPlot` for rendering.
5. All source files in `src/alpha_kd/` remain strictly under the 150-line limit.

---

## Narrative Report
*(To be completed by Claude Code upon execution)*
