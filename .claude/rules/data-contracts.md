# Ingestion & Modeling Data Contracts

- Data Format Integrity: Standardize all internal streaming and historical data structures to formal OHLC/bar schemas.
- Regime Detection Safety: HMM states and MarketDownRegimeAnalyzer outputs must map to distinct, validated data types before passing downstream to execution modules.
