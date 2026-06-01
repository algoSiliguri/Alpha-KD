# Alpha-KD: Grounded Strategic Architecture Decision (v2 — Git-Driven)

> **Date:** 2026-06-01  
> **Analyst:** Hermes (multi-agent orchestrator)  
> **Basis:** Live repository inspection of `algoSiliguri/Alpha-KD`  
> **Constraint:** Zero-AI-slop, incremental greenfield, human GO/ACK gates, GitHub as shared truth

---

## 1. What We Found (Repository Archaeology)

The `Alpha-KD` repository is a **functionally rich but structurally fragile** quant trading system. It contains real intellectual property — regime detection, backtesting, live trading — but the code is organized like a research notebook that accidentally became production.

### The Numbers
- **91 Python files**, **~8,532 lines** of code
- **76 wildcard imports** (`from X import *`) — makes refactor tracing nearly impossible
- **32 hardcoded `pd.read_csv()` calls** — paths baked into source, no config layer
- **~28 launcher scripts** that are 95% copy-paste (7 strategies × 4 validation methods)
- **2 broker stacks** (MetaTrader5 for forex, Upstox for India equities) with **zero abstraction**
- **8 `plt.show()` calls** — will deadlock any headless server or CI pipeline
- **Strategy logic duplicated** in both `Strategies/` (class-based) and `LiveTradingSignal.py` (function-based)
- **No Python package structure** — flat scripts with relative imports and one `sys.path` hack
- **Quantreo/MetaTrader5.py shadows the pip package** — import collision debt
- **Credentials in source code** — `upstox_auth.py`, `execute_cci_strategy.py`, etc.
- **Data committed to git** — 52MB `instruments.json`, CSV bar files

### The Good News
- **Working backtest engine** with CPCV, Monte Carlo, Walk-Forward Optimization
- **Live trading wrappers** that actually place orders (high risk = high value)
- **Regime detection module** with HMM and Markov switching — connects directly to KAIROS learnings
- **Strategy classes have a consistent interface** (`get_entry_signal`, `get_exit_signal`) — we can build on this
- **CLAUDE.md already exists** at root + subdirectories, plus `.claude/rules/` — the user has already been using Claude Code with discipline

---

## 2. The Product Vision: Alpha-KD Live Intelligence

Alpha-KD is not a backtester. It is a **live-market regime-aware risk intelligence engine**.

### The One-Sentence Vision
> "Tell me what the market regime is right now, what my strategies think, and whether I should be in or out — before I lose money."

### Why This Vision (Grounded in the Code)
- The repo already has `regime_detection/` (HMM/Markov) AND `MarketDownRegimeAnalyzer/` (decline thresholds) — but they do not talk to each other.
- The repo already has 7 strategies with validation frameworks — but no regime-aware position sizing or kill switches.
- The repo already has live trading connectors — but no risk-layer between signal and order.

**The gap is not more strategies. The gap is a decision layer.**

### Phase Roadmap (Gradual, Live-Market Focused)

| Phase | Goal | Live-Market Ready? |
|-------|------|-------------------|
| **P1: Foundation** | Package structure, config layer, broker abstraction, ONE strategy proof-of-concept | No (internal-only) |
| **P2: Regime Bridge** | Connect regime detection to execution: "Bull/Bear/Sideways" → position size multiplier | Yes (paper) |
| **P3: Risk Shell** | Dynamic fractional Kelly, peak-to-trough drawdown breaker, shadow fee accounting | Yes (paper) |
| **P4: UI Surface** | Antigravity 2.0 dashboard: regime state, signal status, recommended action, narrative report | Yes (live) |
| **P5: Live Bridge** | Broker order routing with regime-gated kill switch | Yes (live) |

**Rule:** No Phase N+1 work until Phase N produces a novice-readable report proving it works.

---

## 3. The Architecture Decision: GitHub as Shared Truth

### The Problem with the Old Model
Hermes writing local docs and waiting for a manual "GO" signal creates friction. You become the copy-paste middleman between Telegram and your local terminal.

### The Fix: GitHub is the Kanban Board
The repository IS the state machine. Issues, branches, commits, and PRs are the coordination protocol.

```
┌─────────────────────────────────────────────────────────────┐
│  YOU (Telegram)                                             │
│  "Build P1" → Hermes authors plan → You say "GO"            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (Hermes pushes plan to GitHub)
┌─────────────────────────────────────────────────────────────┐
│  GITHUB REPO (Shared Truth)                                 │
│  - Branch: feature/p1-package-contract                      │
│  - Issue #N: P1 execution checklist                         │
│  - File: docs/plans/P1_package_and_contract.md              │
│  - File: CLAUDE.md (execution contract)                     │
│  - File: AGENTS.md (orchestration contract)                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (Claude Code reads branch, executes)
┌─────────────────────────────────────────────────────────────┐
│  CLAUDE CODE (Local)                                        │
│  Reads plan → executes unchecked tasks → checks them off    │
│  → commits → pushes branch                                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼ (You review PR, merge when satisfied)
┌─────────────────────────────────────────────────────────────┐
│  YOU (GitHub PR Review)                                     │
│  Approve / Request changes / Merge                          │
└─────────────────────────────────────────────────────────────┘
```

### Agent Contracts

#### Hermes (Telegram) — Product & Vision Layer
- **Territory:** `docs/plans/`, `docs/ADRs/`, `docs/reports/`, GitHub Issues
- **Reads:** `AGENTS.md`
- **Writes:** Markdown plans, opens GitHub Issues, pushes to feature branches
- **Never:** writes code, executes tests, touches `alpha_kd/`
- **Output:** A GitHub Issue with a checkbox checklist + a feature branch with the plan file

#### Claude Code — Execution Layer
- **Territory:** `alpha_kd/`, `apps/`, `scripts/`, `tests/`
- **Reads:** `CLAUDE.md` + `docs/plans/*.md` + GitHub Issue checklist
- **Executes:** implementation plans task-by-task, checks off items in the Issue
- **Never:** writes plans, changes vision, modifies `docs/ADRs/`
- **Rule:** TDD for every task. Commit after every task. Push after every commit.

#### Antigravity 2.0 — Frontend Layer
- **Territory:** `apps/web/` (to be created in P4)
- **Reads:** `apps/api/` OpenAPI spec
- **Never:** touches `alpha_kd/` directly
- **Contract:** Consumes only the API. The API is the firewall.

### The Handoff Protocol (Zero-Friction)

```
1. You (Telegram): "Build P1"
2. Hermes → GitHub:
   - Creates branch: feature/p1-package-contract
   - Writes: docs/plans/P1_package_and_contract.md
   - Opens: GitHub Issue #N with checkbox checklist
   - Pushes branch
3. You (Terminal): "Claude, sync branch feature/p1-package-contract and execute"
4. Claude Code → Local:
   - Pulls branch
   - Reads plan + Issue checklist
   - Executes unchecked tasks
   - Checks them off in the Issue (via git commit message or manual update)
   - Commits after every task
   - Pushes branch
5. You (GitHub): Review PR, approve/merge
6. Hermes → Telegram: "P1 complete. Ready for P2 planning?"
```

**You only touch two things:** Telegram (vision) and GitHub PR review (quality gate). Everything else is agent-to-agent via the repo.

---

## 4. Target Structure (Incremental Migration)

```
alpha-kd/
├── alpha_kd/                      # NEW: Python package (was loose scripts)
│   ├── __init__.py
│   ├── config.py                  # Immutable constants, env vars, thresholds
│   ├── data/
│   │   ├── features.py            # Was Quantreo/DataPreprocessing.py
│   │   ├── ingestion.py           # Was Data/, Upstox/ fetchers
│   │   └── contracts.py           # OHLC schema, regime schema
│   ├── engine/
│   │   ├── backtest.py            # Was Quantreo/Backtest.py
│   │   ├── metrics.py             # Was Quantreo/Metrics.py + MetricsUtility.py
│   │   ├── cpcv.py                # Was Quantreo/CombinatorialPurgedCV.py
│   │   ├── monte_carlo.py         # Was Quantreo/MonteCarlo.py
│   │   └── wfo.py                 # Was Quantreo/WalkForwardOptimization.py
│   ├── strategies/
│   │   ├── base.py                # NEW: unified Strategy interface
│   │   ├── rsi_sma.py             # Was Strategies/LI_2023_02_RsiSma.py
│   │   ├── ichimoku.py            # Was Strategies/LI_2023_02_Ichimoku_1.py
│   │   └── ... (one per strategy)
│   ├── regime/
│   │   ├── base.py                # NEW: unified RegimeModel interface
│   │   ├── hmm.py                 # Was regime_detection/hidden_markov_model.py
│   │   ├── markov.py              # Was regime_detection/markov_switching_model.py
│   │   └── decline.py             # Was MarketDownRegimeAnalyzer/DeclineAnalyzer.py
│   ├── execution/
│   │   ├── broker.py              # NEW: abstract Broker base class
│   │   ├── mt5.py                 # Was Quantreo/MetaTrader5.py (renamed!)
│   │   ├── upstox.py              # Was Upstox/upstox_live_tradingAPI.py
│   │   └── signal_adapter.py      # NEW: bridges Strategy → live signal
│   └── telemetry/
│       ├── narrative.py           # NEW: plain-English report generator
│       └── logger.py              # NEW: JSONL execution logger
├── apps/
│   └── api/                       # NEW: FastAPI thin wrapper
│       └── main.py
├── scripts/                       # NEW: replaces 28 copy-paste launchers
│   ├── backtest.py
│   ├── cpcv.py
│   ├── monte_carlo.py
│   ├── wfo.py
│   └── live.py
├── notebooks/                     # RETAIN: moved from root Notebooks/
├── data/                          # NEW: external data directory (gitignored)
│   └── .gitkeep
├── tests/                         # NEW: pytest suite
│   └── ...
├── docs/
│   ├── ADRs/                      # Architecture Decision Records
│   ├── plans/                     # Epic plans (Hermes territory)
│   └── reports/                   # Narrative outputs (execution proof)
├── .github/
│   └── ISSUE_TEMPLATE/
│       └── epic.md                # Template for agent-executable epics
├── .env.example
├── pyproject.toml                 # NEW: package metadata
├── CLAUDE.md                      # Claude Code execution contract
├── AGENTS.md                      # Hermes orchestration contract
└── docker-compose.yml             # One-command local stack
```

### Migration Rule
1. Create new file in `alpha_kd/`
2. Copy logic verbatim (zero logic changes)
3. Run old + new in parallel, diff outputs
4. Delete old only after verification passes
5. New features get their own module — never append to existing ones

---

## 5. First Epic: P1 "Package & Contract" (Proof-of-Concept)

**Goal:** Transform loose scripts into a structured Python package with agent contracts, starting with ONE strategy to prove the contract works.

**Why first:** Without this, every agent works on a different mental model of the codebase. The package structure IS the contract.

**Why ONE strategy:** Bulk-migrating all 7 strategies at once risks breaking the legacy path before the new path is proven. One strategy proves the interface. The other 6 follow in P1.5.

### Tasks (bite-sized, 2-5 min each)

1. **Create `pyproject.toml`** — package metadata, dependencies, entry points
2. **Create `alpha_kd/config.py`** — env var loader via `python-dotenv`, zero secrets in source
3. **Create `alpha_kd/strategies/base.py`** — `Strategy` ABC with `get_entry_signal`, `get_exit_signal`
4. **Create `alpha_kd/strategies/rsi_sma.py`** — migrate `RsiSma` class to new package, prove the contract
5. **Create `tests/test_strategies.py`** — pytest verifying `RsiSma` implements `Strategy` ABC correctly
6. **Write `docs/reports/P1_report.md`** — novice-readable narrative proving the contract works

**Estimated:** 6 tasks, ~25 min execution time with Claude Code.

**Success Criteria:**
- `python -m pytest tests/test_strategies.py` passes
- `python -c "from alpha_kd.strategies.rsi_sma import RsiSma; print('OK')"` works
- No `import *` in any new file
- All secrets externalized to `.env.example`

---

## 6. Anti-Patterns We Are Explicitly Rejecting

| Anti-Pattern | Why We Reject | Current Offender |
|-------------|---------------|-----------------|
| Monolithic files >300 lines | Untestable, unnavigable | `CombinatorialPurgedCV.py` (479 lines) |
| Copy-paste launchers | 28 files for 4 patterns | `Launching (CPCV)/`, `Launching (MC)/`, etc. |
| Strategy logic in two places | Maintenance nightmare | `Strategies/` + `LiveTradingSignal.py` |
| `plt.show()` in library code | Deadlocks headless servers | `Backtest.py`, `Metrics.py` |
| Credentials in source | Security debt | `upstox_auth.py`, `execute_cci_strategy.py` |
| Data in git | Bloated repo, non-portable | `Data/`, `utils/instruments.json` |
| `import *` | Breaks refactor tooling | 76 occurrences |
| Manual middleman handoff | You become the bottleneck | Old Hermes proposal |

---

## 7. Decision Gate

**This document is a proposal.** No files have been written. No code has been executed.

To proceed:
- **GO** — Initialize branch `feature/p1-package-contract`, push plan + contracts, open GitHub Issue
- **ACK** — Architecture accepted, but redirect first epic priority
- **TWEAK** — Modify specific sections before proceeding
- **STOP** — Halt, propose alternative

The repository is cloned at `/opt/data/workspace/alpha-kd-inspect/` for inspection.
