# UI-First Readiness Assessment — Alpha-KD at P1

**Date:** 2026-06-01  
**Assessor:** Hermes Agent (Subagent)  
**Scope:** Determine whether building a web dashboard at P1 is premature, and what the minimum viable observability layer looks like now.  
**Reference Skill:** `incremental-greenfield-development` v1.1.0  

---

## 1. What Is the "Hermes Dashboard"?

The user references the **Hermes dashboard** (`hermes dashboard`) as a masterpiece of observability. It is a local web UI served at `127.0.0.1:9119` that provides:

- **Agent status & session observability** — live view of what the agent is doing
- **Kanban task tracking** — visual pipeline of delegated subagent work
- **Configuration surface** — env vars, skills, profiles
- **Extensibility** — plugins, webhook integrations, gateway logs

**Key insight:** The Hermes dashboard is valuable because it observes a *running system* with actual work to display. It did not exist before the agent had tasks, sessions, and a gateway to monitor.

---

## 2. Alpha-KD P1 State — What Exists Now

| Component | Status | What It Produces |
|:---|:---|:---|
| `alpha_kd` package | ✅ Created | Installable Python package |
| `Strategy` ABC | ✅ Created | 3-method contract (`get_features`, `get_entry_signal`, `get_exit_signal`) |
| `RsiSma` migration | ✅ Done | 1 strategy implements the contract |
| Tests | ✅ 3/3 passing | Contract validation only (type/shape checks) |
| Config layer | ✅ Created | Env-var based paths & defaults |
| Backtester | ❌ Missing | No loop that feeds data through a strategy and collects P&L |
| Regime engine | ❌ Missing | P2 scope — not connected |
| Live data feed | ❌ Missing | No streaming or historical ingestion in new package |
| Metrics export | ❌ Missing | `Quantreo/Metrics.py` exists but is NOT wired to `Strategy` ABC |
| Strategy registry | ❌ Missing | No runtime discovery of available strategies |

**What a dashboard would display today:**
- Static parameters for one strategy (`fast_sma=10`, `slow_sma=20`, ...)
- A green checkmark saying "3/3 tests passed"
- A synthetic signal plot on random data
- Nothing else — no trades, no P&L, no regime state, no comparison matrix

---

## 3. The Anti-Pattern Is Real

From `incremental-greenfield-development` (line 74):

> ❌ **Building dashboards, backtesters, or visualizations before the core math primitive works**

**Why this applies to Alpha-KD right now:**

1. **The math primitive is not complete.** The `Strategy` ABC defines an interface, but there is no *engine* that runs it. A dashboard needs an engine producing metrics.
2. **One strategy is not a system.** A dashboard with one card is a profile page, not a control center.
3. **No data pipeline = no observability.** Observability implies observing something happening. At P1, nothing is happening yet.
4. **UI debt compounds.** Every button, route, and widget added now must be maintained while the backend contract is still shifting (P1.5 will add 6 more strategies, P2 will add regime hooks).

---

## 4. Is There an Exception for Telemetry/Observability?

**Yes — but telemetry is not a dashboard.**

The skill forbids *dashboards* (visual, interactive, web-based UIs) before the core math works. It does **not** forbid instrumentation.

| Layer | Appropriate at P1? | Form Factor | Cost |
|:---|:---|:---|:---|
| **Instrumentation / Telemetry** | ✅ Yes | JSONL/CSV/text logs | Near-zero |
| **CI / GitHub Actions** | ✅ Yes | Automated pytest + lint | Near-zero |
| **Narrative reports** | ✅ Yes | Markdown (`docs/reports/`) | Already doing |
| **CLI summary tool** | ⚠️ Maybe | `python -m alpha_kd.status` | Low |
| **Web dashboard (any framework)** | ❌ No | React/Streamlit/Flask | High maintenance |

**The distinction:**
- **Telemetry** = data emitted by the system for later consumption
- **Dashboard** = a UI that consumes data and presents it interactively

Telemetry should be built *into* the primitives so that when the dashboard is built in P2/P3, it has historical data to display.

---

## 5. What the Minimal Observability Layer Looks Like NOW

### Proposal: `alpha_kd/telemetry.py` (text-based, ~60 lines)

A lightweight, append-only JSONL buffer following the **Local Buffer Pattern** from the skill:

```python
# alpha_kd/telemetry.py
import json
import datetime
from pathlib import Path
from typing import Any, Dict

_LOG_PATH = Path(__file__).parent.parent / "logs" / "strategy_runs.jsonl"

def log_run(strategy_name: str, parameters: Dict[str, Any],
            trades: int, signals: int, status: str) -> None:
    _LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.datetime.utcnow().isoformat(),
        "strategy": strategy_name,
        "parameters": parameters,
        "trades": trades,
        "signals": signals,
        "status": status,
    }
    with _LOG_PATH.open("a") as f:
        f.write(json.dumps(entry) + "\n")
```

**What this gives the user today:**
- A human-readable log file tracking every strategy execution
- No web server, no dependencies, no framework
- Consumable by `jq`, `cat`, or a future dashboard

### Proposal: Strategy ABC extension (minimal)

Add two optional hooks to `base.py` so strategies self-report:

```python
class Strategy(ABC):
    ...
    def get_state(self) -> dict:
        """Serialize current position state for observability."""
        return {
            "buy": self.buy,
            "sell": self.sell,
            "open_buy_price": self.open_buy_price,
            "open_sell_price": self.open_sell_price,
        }
```

This is ~5 lines, zero dependencies, and makes the Strategy ABC dashboard-ready for later.

---

## 6. Backend API Surface — What a Dashboard Would Need

| Required API | Exists at P1? | Gap |
|:---|:---|:---|
| List available strategies | ❌ No | Need a registry/discovery mechanism |
| Run backtest & get metrics | ❌ No | Need backtest loop + Metrics integration |
| Get strategy parameters | ⚠️ Partial | Stored in `self.parameters`, no getter |
| Get strategy state | ❌ No | `buy`/`sell` flags are internal |
| Serialize state to JSON | ❌ No | No `to_dict()` methods |
| Stream live data | ❌ No | P5 scope |
| Regime classification | ❌ No | P2 scope |
| Compare strategy performance | ❌ No | Need >1 strategy + backtester |

**Verdict:** The `Strategy` ABC does **not** expose enough surface area for a meaningful dashboard yet. The contract is a *runtime* contract (methods), not a *data* contract (serializable events/metrics).

---

## 7. Concrete Recommendation

### 🔴 DO NOT build a web UI at P1

**Rationale:**
- The incremental-greenfield skill explicitly calls this an anti-pattern
- There is nothing meaningful to observe (1 strategy, no backtester, no live data)
- The Strategy ABC needs a data contract extension before any UI can consume it
- Antigravity 2.0 (or any UI framework) would consume tokens and produce maintenance debt with zero user value today

### 🟢 DO build lightweight telemetry NOW

**Actionable tasks (5-minute increments):**

1. **Add `get_state()` to `Strategy` ABC** — 5 lines, zero deps
2. **Create `alpha_kd/telemetry.py`** — JSONL append-only buffer
3. **Add `logs/` to `.gitignore`** — keep repo clean
4. **Wire telemetry into `RsiSma` test run** — log one entry per test
5. **Add GitHub Action** — run pytest on PRs (free visibility, no token cost)

### 🟡 Wait for P1.5 / P2 before any dashboard

| Phase | When Dashboard Work Starts | Why |
|:---|:---|:---|
| **P1.5** (migrate 6 strategies) | CLI comparison table only | Enough strategies to compare, still no UI needed |
| **P2** (regime detection) | **MINIMAL dashboard becomes viable** | Multiple strategies + regime states = actual data to visualize |
| **P3-P5** (risk + live trading) | Full dashboard with Antigravity 2.0 | Live data, real P&L, configuration surface |

---

## 8. Summary

| Question | Answer |
|:---|:---|
| Is UI-first appropriate at P1? | **No.** It is premature by the skill's own definition. |
| Is observability appropriate at P1? | **Yes.** But as text/JSONL telemetry, not a web UI. |
| Does the Strategy ABC expose enough for a dashboard? | **No.** Needs state serialization + metrics integration first. |
| When should we use Antigravity 2.0? | **P2 minimum**, after regime + backtester are working. |
| What should the user do today? | Add `telemetry.py`, extend `Strategy` with `get_state()`, set up GitHub Actions CI. |

---

*Assessment completed. Recommend presenting this to the user for GO/ACK gate before any files are written.*
