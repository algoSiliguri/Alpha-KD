# Cryptographic & Secret Isolation Rules

- Absolute Prohibition: Plaintext credentials, api_keys, secrets, or access tokens must never exist in application source code.
- Current Risk Audit: Active references found in `Upstox/upstox_auth.py`, `upstox_live_tradingAPI.py`, `main.py`, `Quantreo/IntradayDataAppender.py`, and `LiveTrading/execute_cci_strategy.py` must be treated as architectural debt.
- Target Remediation: All configurations must migrate to an external, gitignored `.env` file. Provide a `.env.example` with blank placeholders only. Never commit active keys in a git diff.
