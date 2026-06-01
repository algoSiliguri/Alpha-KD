import numpy as np
import pandas as pd
import pytest

from alpha_kd.strategies.rsi_sma import RsiSma


@pytest.fixture
def sample_data():
    dates = pd.date_range("2023-01-01", periods=200, freq="h")
    rng = np.random.default_rng(42)
    close = 1.0 + rng.standard_normal(200).cumsum() * 0.01
    delta = rng.standard_normal(200) * 0.005
    data = pd.DataFrame(
        {
            "open": close,
            "high": close + np.abs(delta),
            "low": close - np.abs(delta),
            "close": close,
        },
        index=dates,
    )
    data["high_time"] = data.index
    data["low_time"] = data.index
    return data


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


def test_rsi_sma_implements_strategy(sample_data, params):
    strategy = RsiSma(sample_data, params)
    assert hasattr(strategy, "get_entry_signal")
    assert hasattr(strategy, "get_exit_signal")
    assert hasattr(strategy, "get_features")


def test_rsi_sma_entry_signal(sample_data, params):
    strategy = RsiSma(sample_data, params)
    time = sample_data.index[50]
    signal, entry_time = strategy.get_entry_signal(time)
    assert signal in (-1, 0, 1)


def test_rsi_sma_exit_signal(sample_data, params):
    strategy = RsiSma(sample_data, params)
    time = sample_data.index[50]
    ret, exit_time = strategy.get_exit_signal(time)
    assert isinstance(ret, (int, float))
