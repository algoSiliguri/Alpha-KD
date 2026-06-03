import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from alpha_kd.strategy.rsi_sma import RsiSma
from alpha_kd.telemetry.backtest import BacktestTelemetry


@pytest.fixture
def sample_df():
    dates = pd.date_range("2023-01-01", periods=50, freq="h")
    rng = np.random.default_rng(42)
    close = 1.0 + rng.standard_normal(50).cumsum() * 0.01
    delta = rng.standard_normal(50) * 0.005
    df = pd.DataFrame(
        {
            "open": close,
            "high": close + np.abs(delta),
            "low": close - np.abs(delta),
            "close": close,
        },
        index=dates,
    )
    df["high_time"] = df.index
    df["low_time"] = df.index
    return df


@pytest.fixture
def params():
    return {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }


def test_backtest_telemetry_records_all_bars(sample_df, params):
    with tempfile.TemporaryDirectory() as tmp:
        tel_path = Path(tmp) / "telemetry.jsonl"
        bt = BacktestTelemetry(
            sample_df, RsiSma, params, telemetry_path=tel_path, max_records=10_000
        )
        bt.run()
        lines = tel_path.read_text().splitlines()
        assert len(lines) == len(sample_df)


def test_backtest_telemetry_state_keys(sample_df, params):
    with tempfile.TemporaryDirectory() as tmp:
        tel_path = Path(tmp) / "telemetry.jsonl"
        bt = BacktestTelemetry(sample_df, RsiSma, params, telemetry_path=tel_path)
        bt.run()
        state = bt.buffer.tail(1)[0]
        assert "bar_time" in state
        assert "entry_signal" in state
        assert "exit_return" in state
        assert "side" in state
