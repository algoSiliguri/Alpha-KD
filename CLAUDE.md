# Alpha-KD — Quant Trading System

## Vision
Research-first quant product: backtest, inspect, decide. Not a signal provider,
not an autotrading service. Decoupled domains, single strategy interface,
externalized config, secrets out of source.

## Hard Rules (override defaults)
- NO wildcard imports (`from X import *`). Import named symbols only.
- NO secrets in source. Credentials → env vars / gitignored `.env`. Never commit keys.
- NO new module names that shadow pip packages.
- NO broad refactors without explicit approval.
- Always inspect existing code before editing. Always show a plan before a patch.
- Update the relevant GitHub issue/PR status when task state changes.
- Repo map: `.understand-anything/knowledge-graph.json` (Understand-Anything).
  Prefer it over grep sweeps for structure questions. Refresh after code edits
  if the tooling is available; otherwise note staleness.

## Domain Map
INGESTION  src/alpha_kd/data_fetcher.py, Data/
SIGNAL     src/alpha_kd/strategies/
EXECUTION  src/alpha_kd/execution/
TELEMETRY  src/alpha_kd/telemetry/, src/alpha_kd/backtest_telemetry.py
UI         src/alpha_kd/ui/ (FastAPI backend + Vite/uPlot frontend)

## Debt Status
Original rebuild backlog (wildcard imports, missing package metadata, dual broker
stacks, module/pip name shadow, LI_2023 strategy copy-paste, plaintext credentials)
is RESOLVED — legacy directories removed in commit 16b78b1. Watch for regressions;
do not reintroduce.

## Tooling
- File ops: `rtk read|grep|find|ls`. Heavy sweeps → Explore sub-agent (isolated context).
- Env: uv, pyproject.toml (uv.lock). Python version follows `pyproject.toml`
  (currently >=3.11). FastAPI, onnxruntime, uPlot.

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

### Pre-Push Self-Certification

Before pushing any commit, run the checks below locally and paste the results into the PR description under `## Self-Certification`.

> Full protocol: `docs/ADRs/ADR-002-cost-optimized-review-protocol.md`

```markdown
## Self-Certification

- [ ] `pytest -q` passes locally
- [ ] `ruff check src/ tests/ --select E,W,F` passes (zero errors)
- [ ] Zero lines >88 characters in `src/alpha_kd/` and `tests/`
- [ ] Zero `import *` in new/modified files
- [ ] Zero hardcoded secrets
- [ ] No new monolithic files (>150 lines without ADR justification)
- [ ] Commit messages follow convention
- [ ] Plan deviation noted (if any) with one-sentence justification
```

Quick commands:
```bash
# 1. Clean build + test
uv sync
uv run pytest -q

# 2. Lint (MUST match CI gate exactly)
uv run ruff check src/ tests/ --select E,W,F

# 3. Line-length check (MUST be zero output)
for f in src/alpha_kd/*.py src/alpha_kd/**/*.py tests/*.py; do
  awk -v f="$f" '{if (length > 88) print f ":" NR ": " length " chars"}' "$f"
done

# 4. Import hygiene
grep -r "from .* import \*" src/alpha_kd/ tests/ || echo "No wildcard imports found."

# 5. Secret hygiene
grep -riE "(password|secret|api_key|token)" src/alpha_kd/ tests/ || echo "No obvious secrets found."

# 6. File size check (no file >150 lines)
find src/alpha_kd/ tests/ -name "*.py" -exec wc -l {} + | awk '$1 > 150 {print "OVERSIZE: " $2 " (" $1 " lines)"}'
```

**Rule: If any step produces non-empty output, do not push. Fix it first.**

## Imports
@.claude/rules/python-style.md
@.claude/rules/security.md
@.claude/rules/data-contracts.md

## Local Knowledge Workflow

For complex design, debugging, or planning work, use the local knowledge workflow:

1. Read `wiki/` first — it contains stable, promoted knowledge for this repo.
2. Run `/grill-me` (project skill) to interview one question at a time;
   source playbook: `prompts/grill-me-checkpoint.md`.
3. Save temporary extraction notes in `brainstorms/` (gitignored, local-only).
4. Do not treat `brainstorms/` as durable truth.
5. Promote only stable, approved knowledge into `wiki/` (committed).
6. Run `/promote-to-wiki` (project skill) — requires explicit human approval;
   source playbook: `prompts/promote-to-wiki.md`.
7. Use `artifacts/` only for optional visual summaries (gitignored, local-only).
8. Do not install or use global skills unless explicitly approved.
