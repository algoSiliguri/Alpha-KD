# Cryptographic & Secret Isolation Rules

- Absolute Prohibition: Plaintext credentials, api_keys, secrets, or access tokens must never exist in application source code.
- Status: Historical plaintext-credential debt (legacy `Upstox/`, `Quantreo/`, `LiveTrading/` files) was removed with the legacy directories in commit 16b78b1. No known active violations.
- Standing rule: All configuration lives in an external, gitignored `.env` file. `.env.example` carries blank placeholders only. Never commit active keys in a git diff.
