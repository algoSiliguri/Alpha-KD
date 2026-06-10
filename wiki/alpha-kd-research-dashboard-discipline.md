---
title: Alpha-KD Research Dashboard Discipline
status: verified
tags: [backtest, dashboard, failure-notes, anti-overengineering, research]
created: 2026-06-05
updated: 2026-06-05
source: brainstorms/alpha-kd-research-dashboard-discipline.md, brainstorms/alpha-kd-failure-note-boundaries.md, brainstorms/alpha-kd-minimal-backtest-metrics.md
---

# Alpha-KD Research Dashboard Discipline

One-line: **All research surfaces in Alpha-KD are lightweight audit tools —
inspect and decide, never build and maintain.**

---

## User-Confirmed Decisions

> These were confirmed directly by the user during the grill-me session.

### Failure Notes

- Written **manually**, once per failed strategy attempt.
- Not automated, not auto-logged, not evolved into a tracking system.
- One note per distinct failed strategy config — not one per backtest run.

### Dashboard

- **Passive inspection only.** Opened when you want to see results.
- Not maintained or extended as a product surface.
- "Good enough to read" is the bar — not comprehensive.

### Backtest Metrics

- **Fixed minimal set, defined once** for all strategies.
- A run either passes the bar or it doesn't.
- The set does not grow per strategy or per curiosity.

---

## Boundaries — What This Does NOT Cover

- ~~Does not specify which metrics are in the fixed set~~ → resolved: see Fixed Minimal Backtest Metric Set section below.
- Does not specify where failure notes live on disk — resolved: `docs/failure-notes/`.
- Does not cover live trading surfaces — only research/backtest context.
- Does not govern automated telemetry (`telemetry.jsonl`) — separate concern.

---

## Anti-Patterns (Confirmed)

These are explicitly ruled out by the decisions above:

- Auto-logging every poor backtest result.
- Adding metrics per-curiosity or per new strategy.
- Treating the dashboard as a feature surface to extend.
- Evolving failure notes into a structured tracking system.

---

## Claude Code Recommendations

> [!note] Recommendations — not user-confirmed. Apply only after explicit approval.

- Failure notes directory: `docs/failure-notes/` ✅ confirmed — flat markdown files, one per attempt, named by date + strategy slug.
- Metrics definition: `FIXED_METRIC_KEYS` frozenset in `src/alpha_kd/metrics.py` ✅ confirmed — all backtest runs import from it, no local overrides.
- Dashboard: no new charts or panels unless a specific decision requires it.
  Remove any dashboard code that isn't read at least once per sprint.

---

## Resolved Decisions

> These were confirmed by the user in a follow-up grill-me session (2026-06-05).
> Source: `brainstorms/alpha-kd-failure-note-boundaries.md`

### Failure Note Location

- **`docs/failure-notes/`** — flat markdown files, one per attempt, named by date + strategy slug.
- Fits existing `docs/` structure (`ADRs/`, `plans/`, `reports/`).
- Does not imply product documentation. Does not create a research database.

### Strategy Attempt Boundary

A new failure note is created only when **any of these three conditions** is true:

1. The **hypothesis changes** — a different market assumption is being tested.
2. The **signal, risk, or execution mechanism changes materially** — not just a number, but the mechanism.
3. The **result invalidates a reusable assumption** — something other strategies might depend on.

Parameter tweaks (entry threshold ±5%, lookback 14→20, etc.) within the same hypothesis do **not** get a new note.

---

---

## Fixed Minimal Backtest Metric Set

> Confirmed via grill-me session — 2026-06-05.
> Source: `brainstorms/alpha-kd-minimal-backtest-metrics.md`

### Included (mandatory for every strategy)

| Metric | Key | Already implemented |
|---|---|---|
| Total return | `total_return` | ✅ |
| Max drawdown | `max_drawdown` | ✅ |
| Sharpe ratio | `sharpe_ratio` | ✅ |
| Number of trades | `num_trades` | ✅ |
| Win rate | `win_rate` | ✅ |
| Profit factor | `profit_factor` | ✅ |

### Excluded

These are **explicitly out of scope** for the fixed set. Some are implemented in
`metrics.py` and may be called for ad-hoc analysis, but must not appear in the
standard metrics dict returned by the backtest endpoint.

- `sortino_ratio` — second-order refinement of Sharpe; add only if Sharpe alone proves insufficient
- `drawdown_duration_bars` — diagnostic, not a cross-strategy comparison bar
- `avg_trade_duration_bars` — strategy-specific, not comparable across strategies
- `annualized_return` — period varies; not always meaningful for short backtests
- `avg_trade_return` — redundant with `profit_factor`
- `exposure / time_in_market` — not implemented; regime-adjacent
- `calmar_ratio` — not implemented; excluded until explicitly needed
- Regime-specific metrics — belong to regime analysis, not backtest summary
- Parameter optimization scores — belong to search, not evaluation

### Rationale

Six metrics cover the essential pass/fail bar for any strategy:
- **Risk:** `max_drawdown`
- **Return:** `total_return`
- **Risk-adjusted return:** `sharpe_ratio`
- **Trade quality:** `win_rate`, `profit_factor`
- **Activity:** `num_trades` (sanity check — zero trades = broken strategy)

Small fixed set prevents metric creep: new strategies cannot widen the bar by
adding favorable metrics while hiding unfavorable ones.

### Implementation / Config Location

Fixed set is machine-enforced via a constant in `src/alpha_kd/metrics.py`:

```python
FIXED_METRIC_KEYS = frozenset({
    "total_return",
    "max_drawdown",
    "sharpe_ratio",
    "num_trades",
    "win_rate",
    "profit_factor",
})
```

The backtest endpoint (`src/alpha_kd/ui/backend.py`) imports `FIXED_METRIC_KEYS`
and filters its metrics dict to these keys only.

### Boundaries Against Metric Creep

- Set defined **once** in `metrics.py`. No local overrides.
- Adding a metric requires updating `FIXED_METRIC_KEYS` **and** this wiki section.
- Strategy-specific metrics belong in ad-hoc scripts, not `FIXED_METRIC_KEYS`.
- Dashboard may display additional computed values, but canonical comparison
  surface is the 6-metric fixed set only.

---

## Open Questions

- ~~**Where do failure notes live?**~~ → resolved: `docs/failure-notes/`
- ~~**Strategy attempt boundary.**~~ → resolved: hypothesis/mechanism/assumption boundary (see above)
- ~~**Which metrics are in the fixed set?**~~ → resolved: 6-metric set above; `FIXED_METRIC_KEYS` in `metrics.py`

---

## Next Action

1. ~~Pick a directory for failure notes.~~ → done: `docs/failure-notes/`
2. ~~Define fixed minimal backtest metric set.~~ → done: see section above
3. Add `FIXED_METRIC_KEYS` frozenset to `src/alpha_kd/metrics.py` and filter backend metrics dict.
4. Audit current dashboard code — remove anything not actively read.
