# LiveTrading — Execution (real capital path)

Highest-risk domain: places real orders. Safety over cleverness.

## Rules
- Mock-first: any execution change must be verified against a mock/paper broker before touching a live key.
- No secrets in execution scripts — Live_TEST_CONFIGURATION.py + execute_cci_strategy.py creds migrate to `.env`.
- Explicit broker target: declare MetaTrader5 (forex) vs Upstox (India) per script; never ambiguous routing.
- Idempotent orders: guard against double-submission on retry/restart.
- Position/risk limits must be enforced before order submission, not after.
- Live wrappers configure strategies only — strategy logic stays in Strategies/, not duplicated here.
