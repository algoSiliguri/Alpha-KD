# Alpha-KD — Quant Trading System

## Vision
Robust, backtest-validated trading system. Rebuild target: decoupled domains,
package structure, externalized config, single strategy interface, secrets out of source.

## Hard Rules (override defaults)
- NO wildcard imports (`from X import *`). Import named symbols only.
- NO secrets in source. Credentials → env vars / gitignored `.env`. Never commit keys.
- NO new module names that shadow pip packages (see Quantreo/MetaTrader5.py debt).
- Quantreo/ is the core hub — changes there ripple system-wide; flag blast radius first.
- Two broker stacks exist (MetaTrader5=forex, Upstox=India). State which one a change targets.
- Dirs with spaces ("Launching (CPCV)") — quote paths in shell.
- After code edits, run `graphify update .` if graph exists.

## Domain Map
INGESTION  Upstox/, Upstox_Data/, utils/, Data/
PREPROCESS DenoisingData/, Quantreo.DataPreprocessing
SIGNAL     Strategies/, regime_detection/, MarketDownRegimeAnalyzer/, Quantreo.LiveTradingSignal
VALIDATION Quantreo/{Backtest,CombinatorialPurgedCV,MonteCarlo,WalkForwardOptimization,Metrics}, Launching (*)/
EXECUTION  LiveTrading/, Quantreo.{MetaTrader5,trading_bot}, Upstox live API
MODELS     models/{saved,train}

## Known Debt (rebuild backlog)
1 wildcard imports  2 no package metadata  3 dual broker stacks  4 module/pkg name shadow
5 strategy copy-paste (LI_2023_02_* x7)  6 plaintext credentials

## Tooling
- File ops: `rtk read|grep|find|ls`. Heavy sweeps → Explore sub-agent (isolated context).
- Env: pip, requirements.txt (no lockfile). Python 3, pandas 1.5.3 / sklearn 1.2.2.

## Execution Contract (Agent Protocol)

You are the execution layer. Your job is to read plans from GitHub, implement them task-by-task, and push commits back. You do not write plans. You do not change vision.

### How to Start
When the user says: *"Sync branch feature/XXX and execute"*

1. `git fetch origin`
2. `git checkout feature/XXX` (or `git checkout -b feature/XXX origin/feature/XXX`)
3. Read `docs/plans/PHASE_NAME.md`
4. Read the associated GitHub Issue checklist
5. Execute unchecked tasks in order

### How to Execute a Task
1. Read the task description in the plan file
2. Implement the code/test/docs
3. Run the verification command from the task
4. If verification passes: check off the task in the GitHub Issue
5. Commit: `git add -A && git commit -m "type: description"`
6. Push: `git push origin feature/XXX`
7. Move to next unchecked task

### Commit Convention
```
build:   pyproject.toml, dependencies
feat:    new code, new modules
test:    tests, test data
docs:    documentation, reports
fix:     bug fixes
refactor: code restructuring with no behavior change
```

### Rules
1. **TDD for every task that produces code.** Write failing test → implement → verify pass.
2. **Commit after every task.** No bulk commits.
3. **Push after every commit.** The branch is the progress bar.
4. **No `import *`.** Explicit imports only.
5. **No secrets in source.** Use `alpha_kd.config` or env vars.
6. **No `plt.show()` in library code.** Return figures or save to disk.
7. **If a task fails, stop and report.** Do not proceed to the next task. Comment on the GitHub Issue with the error.
8. **Never modify `docs/plans/` or `docs/ADRs/`.** Those are Hermes territory.
9. **Write `docs/reports/PHASE_report.md` after the last task.** Novice-readable narrative.

### Anti-Patterns
- ❌ Writing a plan file
- ❌ Changing the architecture without asking
- ❌ Skipping tests
- ❌ Bulk commits
- ❌ Modifying `AGENTS.md`

## Imports
@.claude/rules/python-style.md
@.claude/rules/security.md
@.claude/rules/data-contracts.md
