# Phase 6: Single-Platform Control Hub Narrative Report

## Overview
Phase 6 transitions the Alpha-KD platform from a passive backtest/portfolio viewer into an interactive Single-Platform Control Hub. It enables live, dynamic control of multiple execution horizons (Historical Backtest, Forward Test, and Paper Trading) from a glassmorphic Web UI dashboard, with a thread-safe control system, data-loading status guardrails, and a global circuit breaker.

---

## 1. Unified Control Panel & Glassmorphic UI
- **Minimalist Glass Header**: The dashboard is updated with a sleek Control Panel containing an **Execution Mode Dropdown** and tactile buttons: **Start Stream**, **Pause Stream**, and a prominent red **FORCE HALT** button.
- **Tactile Inputs**: Active modes and action states are synced back to the server using standard HTTP POST requests (`/api/control`), which dynamically updates inputs, disables/enables interactive elements, and triggers state transitions.
- **Visual Feedback**: The system displays a live status pulse badge showing `STATUS: LOADING` in orange when data fetching is active, `HALTED` in red, or `ACTIVE` in green.

---

## 2. Dynamic Execution Horizon & Data Loader
- **No-Bloat Architecture**: To prevent `__main__.py` from exceeding the 150-line boundary, we decoupled execution horizon details into a dynamic helper module `alpha_kd/data/loader.py`.
- **Mode-Specific Data Rules**:
  - `'Historical Backtest'`: Fetches 1 month of historical 1-hour bar data. Replays at 0.05 seconds per bar.
  - `'Forward Test (Simulated Live)'`: Fetches 5 days of 1-hour bar data. Replays at 0.5 seconds per bar.
  - `'Paper Trading (Real-Time Live)'`: Fetches 1 day of 1-hour bar data. Updates/steps at 2.0 seconds per bar.
- **Dynamic Transition**: When a user switches modes in the UI, the background thread detects the mode change, truncates the telemetry file, fetches fresh data asynchronously, re-initializes the portfolio engine state, and resets timelines without restarting the process.

---

## 3. Network Hangup Guardrail & Loading Status
- **Loading State Indicator**: Because `urllib.request` is synchronous and can block during API data fetching from Yahoo Finance, we implement a thread-safe `loading = True` status flag.
- **Non-Blocking Render**: While data fetching is running in the background, the server's telemetry endpoint (`/api/telemetry`) continues to serve HTTP GET requests instantly, returning the loading state to the dashboard. The frontend displays a loading overlay, preventing UI freezes or chart frame drops.

---

## 4. Drawdown Breaker Global Halting
- **Instance Registry**: The `DrawdownBreaker` class maintains a registry of active instances using `weakref.WeakSet()`.
- **Global Force Halt**: Clicking the prominent red **FORCE HALT** button triggers a POST request to the server, which invokes `DrawdownBreaker.force_halt_all()`. This instantly flips the `is_halted = True` status of all registered breaker instances in memory, freezing trading activity across all active tickers.

---

## 5. QA & Self-Certification Compliance
- **100% Green Test Suite**: Total of **22 passing tests**. Added detailed unit tests for the data loader (`tests/test_loader.py`), the global force halt breaker registry (`tests/test_risk.py`), and integration endpoints (`tests/test_server.py`).
- **File Length Limits**: Every source code asset (`.py`, `.html`, `.css`, `.js`) stays strictly under the 150-line limit.
- **Clean Lints**: Zero errors from `ruff` or `pytest`.
