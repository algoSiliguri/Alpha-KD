# ADR-002: Cost-Optimized Multi-Agent Review Protocol

**Status:** Proposed  
**Date:** 2026-06-01  
**Decision:** Replace Hermes full line-by-line audits with a "shift-left" gate: Claude self-certification + CI automation + Hermes spot-check tiering.

---

## Context

The P1 review (`PR #26`) required Hermes to read 15 files line-by-line, run tests locally, and author a 97-line narrative report. The review caught one critical bug (`pyproject.toml` broken build backend) and two minor deviations. The token cost was high; the bug should have been caught by automation.

**Goal:** Preserve zero-AI-slop standards while cutting review token spend by ~70%.

---

## Principles

1. **Deterministic work should be done by machines, not tokens.** Lint, test, build, and secret-scan are deterministic. They belong in CI.
2. **Claude Code certifies before Hermes verifies.** Self-certification forces discipline at the source.
3. **Hermes reviews risk, not syntax.** Hermes audits architecture, blast radius, and plan fidelity — the things CI cannot judge.
4. **GitHub is the Kanban board.** All state lives in PR status checks, comments, and Issues. No manual middleman.

---

## 1. Claude Code — Pre-Push Self-Certification

Before every push, Claude Code must run the following locally and paste the results into the PR description under `## Self-Certification`.

### Mandatory Checklist

```markdown
## Self-Certification

- [ ] `pytest` passes locally (attach output snippet)
- [ ] `pip install -e ".[dev]"` succeeds in a clean venv
- [ ] Zero `import *` in new/modified files (`grep -r "from .* import \*" alpha_kd/ tests/`)
- [ ] Zero hardcoded secrets (`grep -riE "(password|secret|api_key|token)" alpha_kd/ || true`)
- [ ] No new monolithic files (>300 lines without ADR justification)
- [ ] Commit messages follow convention (`build|feat|test|docs|fix|refactor:`)
- [ ] Plan deviation noted (if any) with one-sentence justification
```

### How to Run Locally

```bash
# 1. Clean build check
python -m venv /tmp/alpha-kd-clean-venv
source /tmp/alpha-kd-clean-venv/bin/activate
pip install -e ".[dev]"
pytest -q

# 2. Import hygiene
grep -r "from .* import \*" alpha_kd/ tests/ || echo "No wildcard imports found."

# 3. Secret hygiene
grep -riE "(password|secret|api_key|token)" alpha_kd/ tests/ || echo "No obvious secrets found."
```

**Rule:** If any checkbox is unchecked, do not push. Fix it first.

---

## 2. GitHub Actions — CI Gate

Every PR must pass the CI gate before Hermes looks at it. The gate is defined in `.github/workflows/ci-gate.yml`.

### Jobs

| Job | Purpose | Fails on |
|:---|:---|:---|
| `build` | `pip install -e ".[dev]"` in a clean runner | Broken `pyproject.toml`, missing deps |
| `test` | `pytest -q` | Test failures, coverage drop |
| `lint` | `ruff check alpha_kd/ tests/` | `import *`, syntax errors, unused imports |
| `security` | `bandit -r alpha_kd/ -f json` | Hardcoded credentials, unsafe eval |

### Merge Rules

- CI must be **green** before merge.
- Hermes does not review PRs with red CI. He posts: `"Fix CI, then I'll review."`

---

## 3. Hermes — Tiered Review

Hermes does **not** read every line on every PR. He selects a tier based on blast radius.

### Tier Decision Matrix

| Condition | Tier | Hermes Action | Estimated Tokens |
|:---|:---|:---|:---|
| Only `docs/` or `tests/` changed; CI green | **Tier 0 — Trust** | Approve without reading code | ~0 |
| ≤5 files changed; no new domains; CI green | **Tier 1 — Spot-check** | Read diff summary only. Spot-check 1 high-risk file. | ~2k |
| >5 files OR new domain (e.g., `execution/`, `models/`) OR changes `pyproject.toml` / `AGENTS.md` / `CLAUDE.md` | **Tier 2 — Focused audit** | Read diff + all changed files. Verify plan fidelity. | ~8k |
| First PR of a new Phase OR refactor touching >10 legacy files OR security-related | **Tier 3 — Full audit** | Full line-by-line read + local test run + narrative report. | ~25k+ |

### Tier 1 Spot-check Protocol (default)

1. **Read PR description** (self-certification + plan deviation note).
2. **Read the diff stat** (`git diff --stat`).
3. **Spot-check ONE file** using this priority:
   - Any file named `config.py`, `.env.example`, or containing `secret`/`key`/`token`
   - The file with the largest diff
   - Any new `__init__.py` (import hygiene)
4. **Verify plan fidelity:** Did Claude Code follow the checklist in the GitHub Issue?
5. **Post verdict:** `APPROVE`, `COMMENT`, or `REQUEST CHANGES` with ≤5 bullets.

---

## 4. Cost Estimate

### Current Approach (P1 baseline)

| Activity | Tokens | Cost (approx) |
|:---|:---|:---|
| Read 15 files line-by-line | ~15k input | $0.15 |
| Run tests locally + analyze output | ~3k input / 2k output | $0.05 |
| Author narrative report | ~4k input / 3k output | $0.07 |
| **Total per PR** | **~27k** | **~$0.27** |

*Assumes mid-tier model (Sonnet/Kimi), $1 / 1M input tokens, $3 / 1M output tokens.*

### Proposed Approach (typical 3-file PR)

| Activity | Tokens | Cost (approx) |
|:---|:---|:---|
| CI runs (GitHub Actions) | $0 | $0.00 |
| Hermes Tier 1 spot-check | ~2k input / 500 output | $0.02 |
| **Total per PR** | **~2.5k** | **~$0.02** |

### Savings

| Scenario | Old Cost | New Cost | Savings |
|:---|:---|:---|:---|
| Typical PR (3 files, docs/tests only) | $0.27 | $0.00 | **100%** |
| Standard PR (3-5 files, Tier 1) | $0.27 | $0.02 | **93%** |
| Large PR (8 files, Tier 2) | $0.27 | $0.08 | **70%** |
| Phase kickoff (Tier 3 full audit) | $0.27 | $0.27 | **0%** (intentional) |

**Projected monthly savings:** If Alpha-KD averages 10 PRs/month with 1 Phase kickoff, cost drops from ~$2.97 to ~$0.45 (85% reduction).

---

## 5. Trust Preservation

The protocol explicitly addresses the four zero-AI-slop requirements:

| Requirement | How it is preserved |
|:---|:---|
| **No monolithic files** | CI lint job + self-certification checkbox #5 |
| **No secrets** | `bandit` security scan + self-certification checkbox #4 |
| **Explicit imports** | `ruff` lint rule + self-certification checkbox #3 |
| **Catch build bugs** | CI `build` job (`pip install -e`) — would have caught P1 `pyproject.toml` bug |

---

## 6. Rollout

1. **Merge this ADR** to `main`.
2. **Add `.github/workflows/ci-gate.yml`** (see PR).
3. **Update `CLAUDE.md`** with self-certification checklist.
4. **Update `AGENTS.md`** with tiered review matrix.
5. **Next PR:** Hermes enforces Tier 1. If CI is red, review is deferred.

---

*Authored by Hermes Agent*  
*Review model: Tier 3 (protocol design = new domain)*
