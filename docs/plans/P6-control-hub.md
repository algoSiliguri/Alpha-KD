# P6: Single-Platform Control Hub for Multiple Execution Horizons — Execution Plan

> **Epic:** P6 Single-Platform Control Hub  
> **Phase:** P6 (Control & Horizons)  
> **Branch:** `feature/P6-control-hub`  
> **Agent:** Claude Code  
> **Estimated Time:** ~35 minutes  
> **Goal:** Evolve the Alpha-KD dashboard into a unified glassmorphic Control Hub that allows dynamic switching between Historical Backtest, Forward Test, and Paper Trading, with a tactile Start/Pause stream control and an instant FORCE HALT circuit breaker.

---

## Context

We need to transition the Alpha-KD platform from a purely passive backtest/portfolio viewer to an interactive Single-Platform Control Hub.
Our execution is constrained by:
1. MAX LINE COUNT: No single file may exceed 150 lines of code.
2. RISK CONTROLS: The FORCE HALT button must instantly halt all streams by flipping the `is_halted = True` circuit breaker state in `breaker.py`.
3. STATE TRANSITIONS: Standard library utilities only (e.g., `threading.Lock`, `http.server`, etc.).
4. VERIFICATION: Pytest suite must remain 100% green and no files should exceed the 150-line boundary.

---

## Execution Checklist

### Task 1: Add Shared Control State Module
**Objective:** Add `alpha_kd/dashboard/control_state.py` to hold the thread-safe global control state (dropdown execution mode and streaming action) and handle FORCE HALT by setting the circuit breaker's class-level halt state.

**Files:**
- Create: `alpha_kd/dashboard/control_state.py`

**Details:**
- Implement thread-safe control state using standard library `threading.Lock`.
- Provide functions to update and retrieve mode ('Historical Backtest', 'Forward Test (Simulated Live)', 'Paper Trading (Real-Time Live)') and action ('start', 'pause', 'halt').
- If action is `'halt'`, call `DrawdownBreaker.force_halt_all()`.

**Verification:**
```bash
python3 -c "from alpha_kd.dashboard.control_state import get_control; print(get_control())"
```

**Commit:** `feat: implement shared control state module`

---

### Task 2: Refactor DrawdownBreaker for Global Halting
**Objective:** Modify `alpha_kd/risk/breaker.py` to store a class-level variable for global halts and implement `force_halt_all` method.

**Files:**
- Modify: `alpha_kd/risk/breaker.py`
- Modify: `tests/test_risk.py`

**Details:**
- Keep track of all instances in a class-level registry `_instances`.
- When `is_halted` is checked or set, check or set the class-level halt flag.
- Write unit test verifying that calling `force_halt_all()` halts all existing instances immediately.

**Verification:**
```bash
pytest tests/test_risk.py -v
```

**Commit:** `feat: refactor drawdown breaker for instance-level force halting`

---

### Task 3: Refactor BacktestTelemetry for Step-by-Step Execution
**Objective:** Refactor `alpha_kd/telemetry/backtest.py` to expose a `step_one` method to step through individual timestamps.

**Files:**
- Modify: `alpha_kd/telemetry/backtest.py`

**Details:**
- Store the timeline loop states (breaker, ticker_equity, trade_returns, etc.) on `self` in `__init__`.
- Extract the loop body logic into `step_one(self, current_time)`.
- Update `run(self, delay)` to loop over `self.timeline` and call `step_one(current_time)`.
- Verify that existing backtest tests still pass cleanly.

**Verification:**
```bash
pytest tests/test_portfolio.py tests/test_backtest_telemetry.py -v
```

**Commit:** `refactor: refactor BacktestTelemetry to support step_one method`

---

### Task 4: Implement Dynamic Background Execution Loop
**Objective:** Refactor `alpha_kd/__main__.py` to support dynamic execution loops.

**Files:**
- Modify: `alpha_kd/__main__.py`

**Details:**
- Change `run_simulation` to run a continuous dynamic loop.
- Poll the shared control state:
  - If action is `'pause'`, sleep.
  - If mode changes, clear the telemetry file, re-fetch Yahoo Finance data (Historical: 1mo/1h, Forward: 5d/1h, Paper: 1d/1h), re-initialize the `BacktestTelemetry` instance, and reset the bar counter.
  - If action is `'start'`, step one bar and sleep (Historical: 0.05s, Forward: 0.5s, Paper: 2.0s).

**Verification:**
```bash
python3 -c "from alpha_kd.__main__ import run_simulation; print('Engine imports verified')"
```

**Commit:** `feat: implement dynamic execution loop driven by control state`

---

### Task 5: Implement Web Server POST Endpoint for Control Panel
**Objective:** Update `alpha_kd/dashboard/server.py` to support HTTP POST on `/api/control`.

**Files:**
- Modify: `alpha_kd/dashboard/server.py`

**Details:**
- Add `do_POST` handler in `DashboardHandler` to parse incoming JSON and update the shared control state via `update_control(data)`.
- Ensure CORS headers are sent.

**Verification:**
```bash
python3 -c "import alpha_kd.dashboard.server; print('Server module verified')"
```

**Commit:** `feat: add post control endpoint to telemetry server`

---

### Task 6: Update Dashboard UI Controls (HTML/CSS/JS)
**Objective:** Add glassmorphic control panel header, mode selection dropdown, start/pause/halt buttons, and wire POST requests.

**Files:**
- Modify: `alpha_kd/dashboard/static/index.html`
- Modify: `alpha_kd/dashboard/static/style.css`
- Modify: `alpha_kd/dashboard/static/app.js`

**Details:**
- Add control panel header to HTML with elements: dropdown containing modes, buttons for Start Stream, Pause Stream, and FORCE HALT.
- Style these components with clean glassmorphic aesthetics. Ensure `style.css` stays under 150 lines.
- Wire app.js to send POST actions to `/api/control` on button click and dropdown change.

**Verification:**
```bash
# Check that the files parse correctly
python3 -c "open('alpha_kd/dashboard/static/index.html').read()"
```

**Commit:** `feat: integrate glassmorphic control panel header and wire UI actions`

---

### Task 7: Run Self-Certification & QA
**Objective:** Run the full validation suite locally to certify compliance with all development constraints.

**Verification:**
- Run all tests:
  ```bash
  pytest -q
  ```
- Check for line counts:
  ```bash
  find alpha_kd/ tests/ -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" | xargs wc -l | awk '$1 > 150'
  ```
- Run Ruff linting:
  ```bash
  ruff check alpha_kd/ tests/ --select E,W,F
  ```

**Commit:** `test: run self-certification checks`

---

### Task 8: Phase 6 Narrative Report
**Objective:** Author the narrative report summarizing achievements.

**Files:**
- Create: `docs/reports/P6_report.md`

**Commit:** `docs: add phase 6 narrative report`

---

## Success Criteria

1. Minimalist glassmorphic control panel header added to dashboard.
2. Execution mode dropdown offers 'Historical Backtest', 'Forward Test (Simulated Live)', and 'Paper Trading (Real-Time Live)'.
3. Control buttons ('Start Stream', 'Pause Stream', 'FORCE HALT') transmit POST requests to `/api/control`.
4. Control changes dynamically update the data loop feeding the portfolio engine without killing the server.
5. FORCE HALT instantly flips `is_halted = True` on the circuit breaker.
6. All modified and created assets stay strictly under 150 lines.
7. `pytest` passes with 100% green status.

---

## Narrative Report

*Pending execution...*
