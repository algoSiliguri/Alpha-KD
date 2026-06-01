"""Thin I/O: fetch OHLCV from Yahoo Finance, cache to CSV."""
from pathlib import Path
from typing import Optional

import pandas as pd
import yfinance as yf

from alpha_kd.config import DATA_DIR


class YahooFinanceFetcher:
    """Download historical bars from Yahoo Finance with local CSV cache."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = Path(cache_dir or DATA_DIR)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def fetch(
        self,
        symbol: str,
        period: str = "1mo",
        interval: str = "1h",
    ) -> pd.DataFrame:
        """Return OHLCV DataFrame, using cache if available."""
        cache_file = self.cache_dir / f"{symbol}_{interval}_{period}.csv"
        if cache_file.exists():
            return pd.read_csv(cache_file, index_col=0, parse_dates=True)
        ticker = yf.Ticker(symbol)
        df = ticker.history(period=period, interval=interval)
        if df.empty:
            raise ValueError(f"No data returned for {symbol}")
        df.columns = df.columns.str.lower().str.replace(" ", "_")
        # Placeholder columns required by RsiSma.get_exit_signal for intra-bar
        # tie-breaking. Yahoo Finance does not provide intra-bar timestamps, so
        # NaT causes neither branch to execute, safely returning 0.0 instead.
        if "high_time" not in df.columns:
            df["high_time"] = pd.NaT
        if "low_time" not in df.columns:
            df["low_time"] = pd.NaT
        df.to_csv(cache_file)
        return df
