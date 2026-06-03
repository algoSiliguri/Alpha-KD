"""Thin I/O: fetch OHLCV from Yahoo Finance using urllib.request."""
import json
import urllib.request
from pathlib import Path
from typing import Optional

import pandas as pd

from alpha_kd.config import DATA_DIR


class YahooFinanceFetcher:
    """Download historical bars from Yahoo Finance using stdlib urllib.request."""

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

        url = (
            f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}"
            f"?range={period}&interval={interval}"
        )
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req) as response:
                payload = json.loads(response.read().decode())
        except Exception as e:
            raise ValueError(f"Failed to fetch data for {symbol}: {e}")

        result = payload.get("chart", {}).get("result", [])
        if not result:
            raise ValueError(f"No data returned for {symbol}")

        res = result[0]
        timestamps = res.get("timestamp", [])
        if not timestamps:
            raise ValueError(f"No timestamp data found for {symbol}")

        quote = res.get("indicators", {}).get("quote", [{}])[0]
        closes = quote.get("close", [])
        highs = quote.get("high", [])
        lows = quote.get("low", [])
        opens = quote.get("open", [])
        volumes = quote.get("volume", [])

        dt_index = pd.to_datetime(timestamps, unit="s")
        df = pd.DataFrame(
            {
                "open": opens,
                "high": highs,
                "low": lows,
                "close": closes,
                "volume": volumes,
            },
            index=dt_index,
        )
        df.index.name = "Datetime"
        df = df.dropna()

        if "high_time" not in df.columns:
            df["high_time"] = pd.NaT
        if "low_time" not in df.columns:
            df["low_time"] = pd.NaT

        df.to_csv(cache_file)
        return df
