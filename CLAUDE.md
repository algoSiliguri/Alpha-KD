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

## Imports
@.claude/rules/python-style.md
@.claude/rules/security.md
@.claude/rules/data-contracts.md
