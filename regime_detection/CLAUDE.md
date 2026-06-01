# Regime Detection — HMM & Market State

Detects market regimes (HMM) consumed by signal/execution. Mathematical correctness is load-bearing.

## Rules
- HMM state labels are not ordinal — map raw states to named, validated regimes before any downstream use.
- Outputs must conform to the data contract (distinct validated types) before reaching execution (see .claude/rules/data-contracts.md).
- Set and document random_state/seed — regime fits must be reproducible.
- Keep local modules (signal_processor, performance_evaluator) importable without sys.path hacks.
- No look-ahead: regime at bar t may use data up to t only; never future bars.
- MarketDownRegimeAnalyzer shares conventions here — keep state definitions single-source across both.
