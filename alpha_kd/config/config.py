import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

_ROOT = Path(__file__).parent.parent.parent

DATA_DIR = Path(os.getenv("DATA_DIR", _ROOT / "Data"))
MODELS_DIR = Path(os.getenv("MODELS_DIR", _ROOT / "models"))
BROKER_TYPE = os.getenv("BROKER_TYPE", "mt5")
DEFAULT_SYMBOL = os.getenv("DEFAULT_SYMBOL", "EURUSD")
DEFAULT_TIMEFRAME = os.getenv("DEFAULT_TIMEFRAME", "H1")

# Parse TARGET_SYMBOLS env var. Handles JSON array or comma-separated string.
raw_symbols = os.getenv("TARGET_SYMBOLS", "")
if raw_symbols:
    if raw_symbols.strip().startswith("["):
        import json
        try:
            TARGET_SYMBOLS = json.loads(raw_symbols)
        except Exception:
            TARGET_SYMBOLS = [
                s.strip(" '\"")
                for s in raw_symbols.replace("[", "").replace("]", "").split(",")
                if s.strip()
            ]
    else:
        TARGET_SYMBOLS = [s.strip() for s in raw_symbols.split(",") if s.strip()]
else:
    TARGET_SYMBOLS = ["AAPL", "MSFT", "NVDA"]

