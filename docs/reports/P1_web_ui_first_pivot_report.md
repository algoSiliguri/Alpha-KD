# Phase 1/2 Narrative Report: Package Refactor & Web UI First Pivot

This report details the execution of the packaging refactor and the successful implementation of the asynchronous, zero-slop Web UI telemetry platform.

---

## What Was Completed

### 1. Environment & Packaging Overhaul (`uv` + `src/` Layout)
- **Directory Layout Transition:** Moved the `alpha_kd` source package inside `src/alpha_kd` to align with standard production packaging layouts.
- **Dependency Isolation:** Consolidated the dependencies into a modern, hatchling-backed `pyproject.toml`. Core execution runtime dependencies are strictly limited to `fastapi`, `uvicorn`, `websockets`, and `onnxruntime` (for zero-allocation inference). Banned heavy libraries (`pandas`, `scikit-learn`, `matplotlib`, `yfinance`) from the core runtime import path, demoting them strictly to `[project.optional-dependencies].dev` for offline research/backtesting.
- **Environment Locks:** Deleted `requirements.txt` and pinned python version to `3.11` in `.python-version` (necessary for `onnxruntime` wheels on macOS Apple Silicon). Ran `uv sync --all-extras` to lock and build the virtual environment.
- **Git Ignoring Assets:** Added `node_modules/` and `dist/` exclusions inside `.gitignore` and `pyproject.toml` to prevent node modules from polluting python package builds or git tracking.

### 2. High-Performance FastAPI Backend (`src/alpha_kd/ui/backend.py`)
- Created a lightweight FastAPI backend server running out-of-band.
- **Seqlock Telemetry Stream:** Implemented a `/api/telemetry/ws` WebSocket endpoint that maps the shared-memory `mmap` segments, parses tick updates natively using `SeqLock.read_retry` from the `TelemetryHeader` ring buffer, and streams raw bytes directly to connected clients without intermediate python heap allocations.
- **Snapshot Endpoint:** Created an HTTP GET `/api/telemetry/snapshot` endpoint returning the double-buffered snapshot state for initial loads.

### 3. uPlot-Powered Web Frontend Dashboard (`src/alpha_kd/ui/frontend/`)
- Scaffolded a dark-themed single-page dashboard using Vite and `uPlot`.
- Configured binary WebSocket frames (`ArrayBuffer`) and implemented a zero-allocation JS decoder that parses byte offsets directly into a throttled `uPlot` chart rendering at 60fps via `requestAnimationFrame`.

### 4. Backward Compatibility & Test Suite Verification
- Appended the legacy `Strategy` ABC alongside `BaseStrategy` in `src/alpha_kd/strategies/base.py` to prevent breaking existing strategy modules.
- Restored `data_fetcher.py`, `backtest_telemetry.py`, `config.py`, and `__main__.py` under `src/alpha_kd/` to restore CLI functionality and make all tests pass.
- Verified that **all 17 unit/integration tests** pass cleanly.

---

## Validation & Test Results

All tests pass cleanly:
```bash
$ uv run pytest
=================== 17 passed, 1 warning in 3.71s ====================
```

Lints check out cleanly (excluding line length constraints on untouched legacy files):
```bash
$ uv run ruff check src/ --select E,W,F
# Clean formatting & import checks
```

---

## How to Run & Verify

### 1. Launch the Backend Telemetry Server
Run the FastAPI backend with the targeted shared memory session ID:
```bash
uv run python -m alpha_kd.ui.backend --session-id dev-test --port 8000
```

### 2. Build or Run the Frontend App
Navigate to the frontend directory, install node dependencies, and run Vite dev server:
```bash
cd src/alpha_kd/ui/frontend
npm run dev
```
Open `http://localhost:5173/?session-id=dev-test` in the browser to view the real-time uPlot charting dashboard.
