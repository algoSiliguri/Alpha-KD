# P3A Backtest Research Workflow Implementation Plan

**Epic Summary:** Enhance the Legacy Research view of the Alpha-KD dashboard to support side-by-side strategy comparisons, multi-series equity curve overlays, lightweight parameter display, and client-side data exports.

---

## Context
Milestone 3A focuses entirely on improving the Backtest Analysis and Legacy Research workflows. It allows researchers to compare the performance profile of the regime-aware strategy (`RsiSmaRegime`) vs. the baseline strategy (`RsiSma`) side-by-side on real historical data. It facilitates comparison decisions and result exports without modifying live trading code paths or requiring backend database persistence.

---

## Execution Checklist

### Task 1: Update Frontend Layout (`index.html`)
- [ ] Add controls for triggering comparison mode (e.g., "Compare with baseline" checkbox).
- [ ] Add a side-by-side table layout for metric cards.
- [ ] Add UI containers for displaying the default strategy parameters.
- [ ] Add buttons to trigger CSV / JSON exports.
- [ ] Add a visual summary/insights container.

**Verification:**
Verify that the new HTML elements render cleanly by launching the UI locally.

### Task 2: Implement Comparison & Overlay Logic (`main.js`)
- [ ] Implement parallel or sequential fetch logic to fetch data for both strategies if comparison mode is enabled.
- [ ] Adjust `uPlot` dataset building to support overlaying two equity curves.
- [ ] Populate the side-by-side comparison tables.
- [ ] Inject dynamic warning text if observations are fewer than 10 for Sharpe/Sortino ratios.

**Verification:**
Compare metrics visually on the dashboard and ensure both lines render on the equity curve chart with correct scale/legend representation.

### Task 3: Client-Side Result Exports (`main.js`)
- [ ] Add JSON export logic using a serialized browser Blob.
- [ ] Add CSV export logic formatting the `trades` array.

**Verification:**
Click the download buttons and verify that correct `.json` and `.csv` files are generated and contain the expected backtest statistics and trade entries.

### Task 4: UI Styles and Polish (`style.css`)
- [ ] Add styles for side-by-side comparisons, badges, parameters cards, and download buttons.

**Verification:**
Ensure the layouts are fully responsive and fit standard dashboard resolutions.

---

## Success Criteria
- [ ] Side-by-side comparison table showing metrics for both strategies.
- [ ] The `uPlot` chart overlays `RsiSma` vs `RsiSmaRegime` curves when comparison mode is active.
- [ ] Export buttons download correct `.json` (full response) and `.csv` (trades log) files.
- [ ] Current default parameters are displayed for the selected strategies.
- [ ] Summary panels render helpful text (e.g. comparing relative drawdowns and returns).
- [ ] Built frontend assets (`npm run build`) compile without errors.
- [ ] Backend remains unchanged and all unit tests pass (`pytest`).

---

## Narrative Report
*(To be completed by execution agent upon finishing tasks)*
