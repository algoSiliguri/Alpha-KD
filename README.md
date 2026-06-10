# Alpha-KD

Research-first quantitative trading system. Backtest strategies, inspect
results on a local dashboard, decide with evidence.

**What it is:** a personal research product — strategy backtesting, regime
detection, telemetry, and a web dashboard for side-by-side strategy comparison.

**What it is not:** a signal provider, a live autotrading service, or a
broker integration (legacy broker code was removed).

## Architecture

```
src/alpha_kd/
  data_fetcher.py      # INGESTION  — historical/market data
  strategies/          # SIGNAL     — strategy interface + implementations
  execution/           # EXECUTION  — backtest engine, datafeed
  telemetry/           # TELEMETRY  — seqlock ring, structures
  backtest_telemetry.py
  inference/           # ONNX runtime inference
  ui/                  # UI         — FastAPI backend + Vite/uPlot frontend
tests/                 # pytest suite (runs in CI)
docs/plans|ADRs|reports # product plans, decisions, phase reports
```

## Install / run / test

```bash
uv sync                                   # install (Python >=3.11)
uv run pytest -q                          # tests
uv run ruff check src/ tests/ --select E,W,F   # lint (matches CI gate)

# dashboard
uv run uvicorn alpha_kd.ui.backend:app --port 8000   # backend
cd src/alpha_kd/ui/frontend && npm install && npm run dev  # frontend (proxies /api)
```

## Workflow

Phased, epic-driven development:

- **Plans** live in `docs/plans/` (product layer — not edited by execution agents).
- **Epics/stories** are GitHub Issues; PRs gate through CI (`ci-gate.yml`:
  build + pytest + ruff).
- **Phase reports** land in `docs/reports/` after each phase.
- **Agent contract** for execution lives in `CLAUDE.md`; product-layer
  contract in `AGENTS.md`.

## Knowledge

- `wiki/` — promoted, durable product knowledge (committed).
- `prompts/` — intake/promotion playbooks (committed).
- `brainstorms/`, `artifacts/` — local scratch and visuals (gitignored).
- `.understand-anything/` — generated codebase knowledge graph (repo map).
