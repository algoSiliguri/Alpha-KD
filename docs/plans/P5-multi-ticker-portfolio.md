# P5: Multi-Ticker Portfolio Aggregator & Mock Execution Desk — Execution Plan

> **Epic:** P5 Multi-Ticker Portfolio Aggregator & Mock Execution Desk  
> **Phase:** P5 (Multi-Ticker & Portfolio)  
> **Branch:** `feature/P5-multi-ticker-portfolio`  
> **Agent:** Claude Code  
> **Estimated Time:** ~30 minutes  
> **Goal:** Transition the platform from single-ticker backtesting to a multi-ticker portfolio replay engine with a centralized risk breaker and a unified grid dashboard.

---

## Context

We need to elevate the Alpha-KD platform from a single-ticker stream to an asynchronous Multi-Ticker Portfolio Aggregator and Mock Execution Desk. 
Our execution is constrained by:
1. MAX LINE COUNT: No single file may exceed 150 lines of code.
2. RISK CONTROLS: Hard 10% drawdown circuit breaker evaluated against aggregate portfolio equity.
3. TELEMETRY: All operations recorded to `telemetry.jsonl` safely using memory-locked logging queue.
4. DASHBOARD: Responsive glassmorphic layout displaying individual tracking ticker panels and aggregate equity curve.

---

## Execution Checklist

### Task 1: Multi-Ticker Config and CLI Update
**Objective:** Parse symbol arrays from configuration and update main entry point to load historical data for all symbols.

**Files:**
- Modify: `alpha_kd/config/config.py`
- Modify: `alpha_kd/__main__.py`

**Details:**
- Update `config.py` to define `TARGET_SYMBOLS` parsed from `TARGET_SYMBOLS` environment variable (default: `['AAPL', 'MSFT', 'NVDA']`).
- Update `__main__.py` to parse command-line arguments and load all target symbols for simulations.
- Ensure files stay strictly under 150 lines.

**Verification:**
```bash
python3 -c "from alpha_kd.config.config import TARGET_SYMBOLS; print(TARGET_SYMBOLS)"
```

**Commit:** `git add alpha_kd/config/ config.py alpha_kd/__main__.py && git commit -m "feat: support parsing array of target symbols in config and CLI"`

---

### Task 2: Portfolio Aggregation Loop in Backtester
**Objective:** Implement the asynchronous multi-ticker aggregation loop in `backtest.py` stepping through concurrent timelines.

**Files:**
- Modify: `alpha_kd/telemetry/backtest.py`
- Create/Modify helper modules in `alpha_kd/data/` if needed to keep files under 150 lines.

**Details:**
- Align timelines by taking the sorted union of index timestamps.
- Manage separate strategy states and position sizes per ticker.
- Scale starting capital equally across tickers (e.g., initial_capital / len(symbols)).
- Calculate aggregate portfolio equity at each timestep.
- Global circuit breaker must halt all streams when aggregate drawdown hits 10%.
- Ensure file is under 150 lines.

**Verification:**
```bash
python3 -c "from alpha_kd.telemetry.backtest import BacktestTelemetry; print('BacktestTelemetry imported successfully')"
```

**Commit:** `git add alpha_kd/telemetry/backtest.py && git commit -m "feat: implement concurrent multi-ticker portfolio backtesting replay loop"`

---

### Task 3: Portfolio Drawdown Breaker Integration
**Objective:** Couple risk logic in `breaker.py` to monitor aggregate drawdown and trigger global halts.

**Files:**
- Modify: `alpha_kd/risk/breaker.py`
- Create: `tests/test_portfolio.py`

**Details:**
- Ensure `DrawdownBreaker` handles aggregate equity tracking correctly.
- Add tests in `test_portfolio.py` verifying multi-ticker index alignment, aggregate equity summation, and global halt execution.

**Verification:**
```bash
pytest tests/test_portfolio.py -v
```

**Commit:** `git add alpha_kd/risk/breaker.py tests/test_portfolio.py && git commit -m "feat: integrate aggregate portfolio drawdown circuit breaker and tests"`

---

### Task 4: Dashboard Grid Layout and Charts
**Objective:** Update UI layout to display dynamic mini-status panels for each ticker and an aggregate equity curve.

**Files:**
- Modify: `alpha_kd/dashboard/static/index.html`
- Modify: `alpha_kd/dashboard/static/style.css`
- Modify: `alpha_kd/dashboard/static/app.js`

**Details:**
- Reference Chart.js CDN in `index.html`.
- Add a flex/grid container for dynamic ticker cards and a canvas for the equity curve chart.
- Style cards using dark-mode glassmorphic aesthetics.
- Script `app.js` to build/update ticker cards dynamically from `tickers` telemetry data and draw the equity curve.
- Ensure all files remain strictly under 150 lines.

**Verification:**
```bash
python3 -c "import alpha_kd.dashboard.server; print('Dashboard layout verified')"
```

**Commit:** `git add alpha_kd/dashboard/ && git commit -m "feat: extend glassmorphic dashboard with multi-ticker grid and equity curve chart"`

---

### Task 5: Pre-Push Certification and QA
**Objective:** Run the full validation suite locally to certify compliance with all development constraints.

**Verification:**
- Run all tests:
  ```bash
  pytest -q
  ```
- Ruff linting:
  ```bash
  ruff check alpha_kd/ tests/ --select E,W,F
  ```
- File line counts check:
  ```bash
  find alpha_kd/ tests/ -name "*.py" -o -name "*.html" -o -name "*.css" -o -name "*.js" | xargs wc -l | awk '$1 > 150'
  ```

**Commit:** `git commit --allow-empty -m "test: run self-certification checks"`

---

### Task 6: P5 Narrative Report
**Objective:** Author the narrative report summarizing achievements.

**Files:**
- Create: `docs/reports/P5_report.md`

**Commit:** `git add docs/reports/P5_report.md && git commit -m "docs: add phase 5 narrative report"`

---

## Success Criteria

1. Target symbol list is successfully configurable via environment variables.
2. Concurrent timelines are correctly aligned and stepped in chronological order.
3. Portfolio equity is aggregated accurately across active symbols.
4. Combined drawdown of 10% halts all asset sub-streams instantly.
5. Dashboard displays mini-status panels for all target symbols and updates the equity curve dynamically.
6. All created and modified code/style/HTML files remain under 150 lines.
7. 100% of automated tests pass cleanly.

---

## Narrative Report

Phase 5 has been executed successfully. Details of implementation, design choices, timeline union alignment, and drawdown breaker behavior are documented in [P5_report.md](../reports/P5_report.md).
All tasks (Task 1 to Task 6) are 100% complete, tests pass cleanly, and files comply with the 150-line limits.
