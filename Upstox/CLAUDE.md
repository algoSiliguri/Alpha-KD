# Upstox — Ingestion & Broker (India equities)

Isolated broker boundary. Must not leak broker-specific types into core engine or strategies.

## Rules
- Secrets: api_key / api_secret / access_token NEVER in source. Migrate config_reader + upstox_config.properties to gitignored `.env`.
- Active credential references (upstox_auth.py, upstox_live_tradingAPI.py, main.py) are debt — treat as remediation targets, not patterns to copy.
- Broker isolation: this stack is Upstox-only. Do not mix MetaTrader5 / forex execution paths in here.
- Ingested data must conform to the OHLC/bar contract before handoff downstream (see .claude/rules/data-contracts.md).
- Network/auth calls must fail safe — no silent retry loops that could double-submit live orders.
- Keep `Upstox/Historical Data Fetcher/` path quoted in shell (space in dir name).
