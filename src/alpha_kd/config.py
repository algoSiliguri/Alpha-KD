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
