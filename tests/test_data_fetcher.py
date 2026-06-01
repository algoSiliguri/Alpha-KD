import tempfile
from pathlib import Path

import pandas as pd
import pytest

from alpha_kd.data_fetcher import YahooFinanceFetcher


class TestYahooFinanceFetcher:
    def test_fetch_returns_dataframe(self):
        fetcher = YahooFinanceFetcher()
        df = fetcher.fetch("AAPL", period="5d", interval="1d")
        assert isinstance(df, pd.DataFrame)
        assert not df.empty
        assert "close" in df.columns.str.lower()

    def test_cache_creates_csv(self):
        with tempfile.TemporaryDirectory() as tmp:
            cache_dir = Path(tmp)
            fetcher = YahooFinanceFetcher(cache_dir=cache_dir)
            df = fetcher.fetch("AAPL", period="5d", interval="1d")
            cache_file = cache_dir / "AAPL_1d_5d.csv"
            assert cache_file.exists()
            df2 = pd.read_csv(cache_file, index_col=0, parse_dates=True)
            assert len(df2) == len(df)
