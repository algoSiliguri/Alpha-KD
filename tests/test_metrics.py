"""Unit tests for the pure metrics calculations and trade reconstruction layer."""
import pytest
from alpha_kd.metrics import (
    reconstruct_equity_curve,
    calculate_cumulative_returns,
    calculate_max_drawdown,
    calculate_drawdown_duration,
    reconstruct_trades,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
)


def test_flat_only_telemetry():
    """Flat-only telemetry: constant equity, no trades, metrics return safe nulls."""
    records = [
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "timestamp": "2026-06-05T12:00:00Z"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "timestamp": "2026-06-05T13:00:00Z"
        },
    ]
    equity = reconstruct_equity_curve(records, initial_capital=100000.0)
    assert equity == [100000.0, 100000.0]

    cum_returns = calculate_cumulative_returns(equity)
    assert cum_returns == [0.0, 0.0]

    trades = reconstruct_trades(records)
    assert len(trades) == 0

    assert calculate_win_rate(trades) == 0.0
    assert calculate_profit_factor(trades) is None
    assert calculate_max_drawdown(equity) == 0.0
    assert calculate_drawdown_duration(equity) == 0


def test_one_winning_trade():
    """One winning trade: equity increases, win rate = 1.0, PF is None."""
    records = [
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "entry_price": None,
            "timestamp": "T0"
        },
        {
            "side": "buy",
            "unrealized_pnl": 0.01,
            "exit_return": 0.0,
            "entry_price": 100.0,
            "timestamp": "T1"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.02,
            "entry_price": 100.0,
            "timestamp": "T2"
        },
    ]
    equity = reconstruct_equity_curve(records, initial_capital=100000.0)
    # T0: flat -> 100k
    # T1: buy, unrealized_pnl 0.01 -> 101k
    # T2: exit_return 0.02 -> 102k (compounded from last_realized 100k)
    assert equity == [100000.0, 101000.0, 102000.0]

    trades = reconstruct_trades(records)
    assert len(trades) == 1
    assert trades[0]["side"] == "buy"
    assert trades[0]["exit_return"] == 0.02
    assert trades[0]["entry_price"] == 100.0
    assert trades[0]["exit_price"] == 102.0

    assert calculate_win_rate(trades) == 1.0
    assert calculate_profit_factor(trades) is None


def test_one_losing_trade():
    """One losing trade: equity decreases, win rate = 0.0, PF is 0.0."""
    records = [
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "entry_price": None,
            "timestamp": "T0"
        },
        {
            "side": "sell",
            "unrealized_pnl": -0.01,
            "exit_return": 0.0,
            "entry_price": 100.0,
            "timestamp": "T1"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": -0.015,
            "entry_price": 100.0,
            "timestamp": "T2"
        },
    ]
    equity = reconstruct_equity_curve(records, initial_capital=100000.0)
    assert equity == [100000.0, 99000.0, 98500.0]

    trades = reconstruct_trades(records)
    assert len(trades) == 1
    assert trades[0]["exit_return"] == -0.015
    assert calculate_win_rate(trades) == 0.0
    assert calculate_profit_factor(trades) == 0.0


def test_two_trades_win_loss():
    """Two trades: one +2%, one -1%: win rate = 0.5, PF = 2.0."""
    records = [
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "entry_price": None,
            "timestamp": "T0"
        },
        {
            "side": "buy",
            "unrealized_pnl": 0.01,
            "exit_return": 0.0,
            "entry_price": 100.0,
            "timestamp": "T1"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.02,
            "entry_price": 100.0,
            "timestamp": "T2"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": 0.0,
            "entry_price": None,
            "timestamp": "T3"
        },
        {
            "side": "sell",
            "unrealized_pnl": -0.005,
            "exit_return": 0.0,
            "entry_price": 200.0,
            "timestamp": "T4"
        },
        {
            "side": "flat",
            "unrealized_pnl": None,
            "exit_return": -0.01,
            "entry_price": 200.0,
            "timestamp": "T5"
        },
    ]
    # Trade 1 exits with 0.02: 100k -> 102k
    # Trade 2 exits with -0.01: 102k -> 102k * 0.99 = 100980.0
    equity = reconstruct_equity_curve(records, initial_capital=100000.0)
    assert equity[-1] == 100980.0

    trades = reconstruct_trades(records)
    assert len(trades) == 2
    assert calculate_win_rate(trades) == 0.5
    assert calculate_profit_factor(trades) == 2.0


def test_drawdown_calculation():
    """Drawdown case: max drawdown and drawdown duration are verified."""
    equity = [100.0, 110.0, 99.0, 95.0, 105.0, 115.0]
    # Peak at 110.0, troughs at 99.0, 95.0.
    # Max drawdown is (110 - 95) / 110 = 15 / 110 approx 0.13636
    assert calculate_max_drawdown(equity) == pytest.approx(15.0 / 110.0)

    # Peak reached at idx 1 (110.0) and not exceeded until idx 5 (115.0)
    # Drawdown duration: idx 2 (1), idx 3 (2), idx 4 (3). Max duration = 3.
    assert calculate_drawdown_duration(equity) == 3


def test_short_sample_metrics():
    """Fewer than 10 return observations returns None for Sharpe and Sortino."""
    returns = [0.01, -0.005, 0.02]
    assert calculate_sharpe_ratio(returns) is None
    assert calculate_sortino_ratio(returns) is None


def test_valid_sample_metrics():
    """10+ return observations returns numeric values."""
    returns = [
        0.01, -0.005, 0.02, -0.01, 0.005,
        0.015, -0.002, 0.01, -0.008, 0.012
    ]
    assert len(returns) == 10

    sharpe = calculate_sharpe_ratio(returns)
    sortino = calculate_sortino_ratio(returns)

    assert isinstance(sharpe, float)
    assert isinstance(sortino, float)
    assert sharpe != 0.0
    assert sortino != 0.0
