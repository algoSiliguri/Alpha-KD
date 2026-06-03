# P4: UI-First Dashboard & Risk Engine — Execution Plan

> **Epic:** P4 UI-First Dashboard & Risk Engine  
> **Phase:** P4 (UI-First & Risk)  
> **Branch:** `auto/ui-first-complete`  
> **Agent:** Claude Code  
> **Estimated Time:** ~30 minutes  
> **Goal:** Restructure the project into 6 core modules, build a web dashboard (glassmorphism UI, all files <150 lines), implement a 10% drawdown breaker and fractional Kelly sizing, and verify with tests.

---

## Context

We need to build out the Alpha-KD platform using an incremental, UI-First approach with strict rules:
1. MAX LINE COUNT: No single file may exceed 150 lines of code.
2. MODULE BOUNDARIES: Maximum 6-module contract boundary for the entire project.
3. RISK CONTROLS: Hard 10% drawdown circuit breaker and fractional Kelly sizing calculations.
4. TELEMETRY: State changes logged to an append-only JSONL telemetry framework, visible live in the dashboard.

---

## Execution Checklist

### Task 1: Module Restructuring & Initialization
**Objective:** Initialize the 6 core module boundaries as clean directories with stubs and migrate existing modules.

**Files:**
- Create/Modify:
  - `alpha_kd/config/__init__.py` & `alpha_kd/config/config.py` (migrated from config.py)
  - `alpha_kd/data/__init__.py` & `alpha_kd/data/data_fetcher.py` (migrated from data_fetcher.py)
  - `alpha_kd/strategy/__init__.py`, `alpha_kd/strategy/base.py`, `alpha_kd/strategy/rsi_sma_regime.py` (migrated from strategies/)
  - `alpha_kd/risk/__init__.py` (stubs)
  - `alpha_kd/telemetry/__init__.py` (stubs)
  - `alpha_kd/dashboard/__init__.py` (stubs)

**Details:**
- Keep all files under 150 lines.
- Update all internal imports within `alpha_kd/` to point to the new module boundaries.

**Verification:**
```bash
python3 -c "import alpha_kd.config; import alpha_kd.data; import alpha_kd.strategy; import alpha_kd.risk; import alpha_kd.telemetry; import alpha_kd.dashboard; print('Restructuring OK')"
```

**Commit:** `git add alpha_kd/ && git commit -m "refactor: initialize 6-module boundary directories"`

---

### Task 2: Core Risk Engine (Drawdown Breaker & Kelly Sizing)
**Objective:** Implement the hard 10% drawdown circuit breaker and fractional Kelly sizing utilities.

**Files:**
- Create: `alpha_kd/risk/breaker.py`
- Create: `alpha_kd/risk/kelly.py`
- Create: `tests/test_risk.py`

**Details:**
- `breaker.py`: Track peak equity/return. If drawdown from peak exceeds 10% (i.e. return drops by 10% relative to peak or overall), trigger circuit breaker (`is_halted = True`).
- `kelly.py`: Calculate fractional Kelly sizing using the formula: $f^* = f_s \times (p - (1 - p) / b)$ where $p$ is win probability, $b$ is win/loss ratio, and $f_s$ is the scaling fraction (e.g. 0.5 for half-Kelly).
- Ensure all files are under 150 lines.

**Verification:**
```bash
pytest tests/test_risk.py -v
```

**Commit:** `git add alpha_kd/risk/ tests/test_risk.py && git commit -m "feat: implement drawdown circuit breaker and Kelly sizing utilities"`

---

### Task 3: Core Telemetry Integration
**Objective:** Implement the JSONL logging logic and integrate it with state changes.

**Files:**
- Create: `alpha_kd/telemetry/logger.py`
- Create: `tests/test_telemetry.py`

**Details:**
- Write an append-only JSONL log writer that writes state changes, timestamps, current drawdown, Kelly size, and breaker status.
- Truncate logs if they exceed 10,000 records.
- Ensure file is under 150 lines.

**Verification:**
```bash
pytest tests/test_telemetry.py -v
```

**Commit:** `git add alpha_kd/telemetry/ tests/test_telemetry.py && git commit -m "feat: implement JSONL telemetry logging engine"`

---

### Task 4: UI-First Dashboard Scaffolding
**Objective:** Build a modular, premium, responsive frontend dashboard layout (glassmorphism UI, all files <150 lines).

**Files:**
- Create: `alpha_kd/dashboard/server.py`
- Create: `alpha_kd/dashboard/static/index.html`
- Create: `alpha_kd/dashboard/static/style.css`
- Create: `alpha_kd/dashboard/static/app.js`

**Details:**
- `server.py`: Simple python server using `http.server` to serve static UI files and expose telemetry log endpoints.
- `index.html`: Responsive panel layout containing: Strategy Status, Drawdown Tracker, Kelly Monitor, and Live Telemetry Terminal View.
- `style.css`: Glassmorphism styling, dark mode, Outfit/Inter typography, gradients, hover micro-animations.
- `app.js`: Connects to backend, polls telemetry logs, and updates UI status/widgets in real-time.
- EVERY single file must be under 150 lines.

**Verification:**
```bash
python3 -c "import alpha_kd.dashboard.server; print('Dashboard Server OK')"
```

**Commit:** `git add alpha_kd/dashboard/ && git commit -m "feat: build responsive glassmorphic telemetry dashboard layout"`

---

### Task 5: Main Entry Point CLI Integration
**Objective:** Update the main entry point to wire all modules and support launching the dashboard.

**Files:**
- Modify: `alpha_kd/__main__.py`
- Modify: `pyproject.toml` (if entrypoints/dependencies need updating)

**Details:**
- Add `--dashboard` argument to `alpha_kd` entry point. When run, it starts the dashboard server.
- The server will run a background thread feeding mock market tick updates, performing drawdown checks, updating Kelly sizes, and appending to `telemetry.jsonl` so the UI terminal renders live updates.

**Verification:**
```bash
python3 -m alpha_kd --help
```

**Commit:** `git add alpha_kd/__main__.py && git commit -m "feat: wire CLI entrypoint for --dashboard launcher"`

---

### Task 6: Pre-Push Certification & QA
**Objective:** Verify that all code conforms to the project contract guidelines.

**Verification:**
- Run `pytest` to ensure all tests pass.
- Run `ruff check alpha_kd/ tests/ --select E,W,F` (zero errors).
- Check that no file exceeds 150 lines:
  ```bash
  find alpha_kd/ tests/ -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" | xargs wc -l | awk '$1 > 150'
  ```
  Expected: No files listed as over 150 lines.

**Commit:** `git commit --allow-empty -m "test: execute and certify P4 validation suite"`

---

### Task 7: P4 Narrative Report
**Objective:** Write a novice-readable report summarizing the architecture and components.

**Files:**
- Create: `docs/reports/P4_report.md`

**Verification:**
```bash
ls docs/reports/P4_report.md
```

**Commit:** `git add docs/reports/P4_report.md && git commit -m "docs: add P4 narrative report"`

---

## Success Criteria

1. Restructured codebase strictly follows the 6-module boundary.
2. Every file created/modified is under 150 lines.
3. Drawdown breaker triggers and halts trading when cumulative loss exceeds 10%.
4. Sizing calculation handles fractional Kelly scaling.
5. Telemetry terminal updates in real-time on the browser page.
6. The styling of the dashboard matches premium modern standards (dark mode, glassmorphism, responsive).
7. Pytest, Ruff, and size audits pass with zero errors.

---

## Narrative Report

*Pending execution by Claude Code...*
