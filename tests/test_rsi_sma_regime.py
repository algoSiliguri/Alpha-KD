import numpy as np
import pandas as pd
import pytest

from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime


@pytest.fixture
def sample_df():
    dates = pd.date_range("2023-01-01", periods=100, freq="h")
    rng = np.random.default_rng(42)
    close = 100 + rng.standard_normal(100).cumsum()
    df = pd.DataFrame(
        {"open": close, "high": close + 1, "low": close - 1, "close": close,
         "high_time": pd.NaT, "low_time": pd.NaT},
        index=dates,
    )
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


def test_regime_state_key(sample_df, params):
    strategy = RsiSmaRegime(sample_df, params)
    state = strategy.get_state()
    assert "regime" in state
    assert state["regime"] in ("bull", "bear", "sideways", "unknown")
