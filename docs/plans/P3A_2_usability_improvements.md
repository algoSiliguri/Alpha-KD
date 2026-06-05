# P3A.2 Backtest Analysis Usability Improvements

## Epic Summary
Introduce research-usability enhancements to the Backtest Analysis view to make strategy metadata, parameters, and comparison metrics transparent and easy to interpret without adding trading recommendations or live execution dependencies.

## Context
As research workflows expand, comparing `RsiSma` and `RsiSmaRegime` requires clear parameter visibility, neutral metric interpretations (to avoid false signals or optimization traps), and robust result metadata. This milestone focuses entirely on frontend usability, leveraging existing telemetry/backtest REST endpoints without altering any backend logic or zero-alloc streams.

## Execution Checklist

- [ ] **Task 1: Add Parameter Display Section**
  - Read parameters from the stored list returned by `/api/strategies`.
  - Add a dedicated read-only grid layout within the configuration panel to display current parameter keys and values (e.g. `fast_sma`, `slow_sma`, `rsi`, `tp`, `sl`, `cost`, `leverage`).
  - *Verification:* Select a strategy in the dropdown and verify parameters load dynamically.
  
- [ ] **Task 2: Implement Metric Explanation Tooltips**
  - Add small explanation or info icons next to metric cards (Max Drawdown, Profit Factor, Sharpe Ratio, Sortino Ratio).
  - Use simple vanilla CSS hover tooltips or descriptive help text.
  - *Verification:* Hover over "Max Drawdown" and verify tooltip text reads: "Max Drawdown = largest peak-to-trough equity drop."

- [ ] **Task 3: Add Result Metadata Sub-panel**
  - Display strategy ID, strategy name, path (legacy / zero_alloc), status (research_only / stub), bars processed, trade count, alignment method (shortest common length if comparison mode is active), and export timestamp.
  - *Verification:* Run a backtest, verify metadata updates with accurate values and the current timestamp.

- [ ] **Task 4: Add Neutral Research Summary Panel**
  - Add a text panel that programmatically compares the metrics of the primary and comparison strategy (if active).
  - Populate deterministic summary text using approved templates only (e.g., "RsiSmaRegime has lower max drawdown than RsiSma." or "Sharpe ratio is unavailable because there are fewer than 10 observations.").
  - *Verification:* Ensure no forbidden recommendation words (winner, best, recommended, buy, sell, alpha confirmed, live-ready) are present.

- [ ] **Task 5: Verify Build and Integration**
  - Build front-end assets using `npm run build` to ensure no syntax/compilation issues.
  - Verify that `telemetry.jsonl` remains untouched.
  - *Verification:* Run backend and frontend dev server to check full end-to-end integration without errors.

## Success Criteria
- Primary and comparison strategy parameters are displayed clearly upon strategy selection.
- Metric explanation tooltips are visible and accurate on hover.
- Result metadata updates correctly on run.
- Neutral research summary panel provides purely deterministic comparisons without trade advice.
- No modifications made to the backend or `telemetry.jsonl`.

## Narrative Report
*To be populated upon task completion.*
