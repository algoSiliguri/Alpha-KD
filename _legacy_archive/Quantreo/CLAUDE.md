# Quantreo — Core Engine (system hub)

Every domain imports inward here. Treat as a stable API; breaking changes ripple everywhere.

## Rules
- God-modules: CombinatorialPurgedCV.py (19K), WalkForwardOptimization.py (16K). Refactor in slices, never big-bang.
- Export named symbols only; callers must stop using `import *` — do not add new wildcard surface.
- MetaTrader5.py shadows the pip package — rebuild renames this (e.g. mt5_adapter.py); do not deepen the collision.
- Backtest / CPCV / MonteCarlo / WFO share Metrics + MetricsUtility — keep metric definitions single-source, no duplication.
- Any change here: state blast radius (which downstream domains import the touched symbol) before editing.
- Preserve numerical behavior of validation math; gate changes behind a reproducible backtest comparison.
