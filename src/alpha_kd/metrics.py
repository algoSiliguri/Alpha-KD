"""Pure metrics utility module for Alpha-KD dashboard calculations.

This module contains pure functions for reconstructing equity curves,
calculating risk/performance metrics, and trade reconstruction from telemetry.
"""
import math
from typing import List, Dict, Any, Optional


def reconstruct_equity_curve(
    telemetry_records: List[Dict[str, Any]],
    initial_capital: float = 100000.0
) -> List[float]:
    """Reconstructs the equity curve from telemetry records.

    Applies exit returns and unrealized P&L correctly without blind compounding.
    """
    if not telemetry_records:
        return []

    equity = []
    last_realized_equity = initial_capital

    for i, record in enumerate(telemetry_records):
        side = record.get("side", "flat")
        unrealized_pnl = record.get("unrealized_pnl")
        exit_return = record.get("exit_return", 0.0)

        if exit_return is None:
            exit_return = 0.0

        if exit_return != 0.0:
            # Trade exited on this bar
            current_equity = last_realized_equity * (1.0 + exit_return)
            last_realized_equity = current_equity
        elif side in ("buy", "sell") and unrealized_pnl is not None:
            # Trade is open
            current_equity = last_realized_equity * (1.0 + unrealized_pnl)
        else:
            # Flat period or missing unrealized pnl
            if i == 0:
                current_equity = initial_capital
            else:
                current_equity = equity[-1]

        equity.append(current_equity)

    return equity


def calculate_cumulative_returns(equity_curve: List[float]) -> List[float]:
    """Calculates cumulative return percentage at each point of the equity curve."""
    if not equity_curve:
        return []
    base_equity = equity_curve[0]
    if base_equity == 0.0:
        return [0.0] * len(equity_curve)
    return [(val - base_equity) / base_equity for val in equity_curve]


def calculate_max_drawdown(equity_curve: List[float]) -> float:
    """Calculates the maximum drawdown percentage from the equity curve peak."""
    if not equity_curve:
        return 0.0
    peak = equity_curve[0]
    max_dd = 0.0
    for val in equity_curve:
        if val > peak:
            peak = val
        if peak > 0.0:
            dd = (peak - val) / peak
            if dd > max_dd:
                max_dd = dd
    return max_dd


def calculate_drawdown_duration(equity_curve: List[float]) -> int:
    """Calculates the maximum drawdown duration in number of bars."""
    if not equity_curve:
        return 0
    peak = equity_curve[0]
    current_duration = 0
    max_duration = 0
    for val in equity_curve:
        if val >= peak:
            peak = val
            current_duration = 0
        else:
            current_duration += 1
            if current_duration > max_duration:
                max_duration = current_duration
    return max_duration


def reconstruct_trades(telemetry_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Reconstructs completed trades from telemetry snapshots."""
    trades = []
    active_trade = None

    for i, record in enumerate(telemetry_records):
        side = record.get("side", "flat")
        bar_time = record.get("bar_time", record.get("timestamp"))
        entry_price = record.get("entry_price")
        exit_return = record.get("exit_return", 0.0)

        if exit_return is None:
            exit_return = 0.0

        regime = record.get("regime", "unknown")

        if active_trade is None:
            if side in ("buy", "sell"):
                active_trade = {
                    "entry_time": bar_time,
                    "side": side,
                    "entry_price": entry_price,
                    "regime_at_entry": regime,
                    "entry_idx": i
                }
        else:
            is_exit = (
                (exit_return != 0.0)
                or (side == "flat")
                or (side != active_trade["side"])
            )

            if is_exit:
                closed_trade = {
                    "entry_time": active_trade["entry_time"],
                    "exit_time": bar_time,
                    "side": active_trade["side"],
                    "entry_price": active_trade["entry_price"],
                    "exit_price": (
                        active_trade["entry_price"] * (1.0 + exit_return)
                        if active_trade["entry_price"] is not None
                        else None
                    ),
                    "exit_return": exit_return,
                    "regime_at_entry": active_trade["regime_at_entry"],
                    "duration_bars": i - active_trade["entry_idx"]
                }
                trades.append(closed_trade)

                if side in ("buy", "sell") and side != active_trade["side"]:
                    active_trade = {
                        "entry_time": bar_time,
                        "side": side,
                        "entry_price": entry_price,
                        "regime_at_entry": regime,
                        "entry_idx": i
                    }
                else:
                    active_trade = None

    return trades


def calculate_win_rate(trades: List[Dict[str, Any]]) -> float:
    """Calculates win rate (profitable trades / total trades)."""
    if not trades:
        return 0.0
    wins = sum(1 for t in trades if t.get("exit_return", 0.0) > 0.0)
    return wins / len(trades)


def calculate_profit_factor(trades: List[Dict[str, Any]]) -> Optional[float]:
    """Calculates the profit factor. Returns None if there are no losses."""
    wins = [
        t.get("exit_return", 0.0)
        for t in trades
        if t.get("exit_return", 0.0) > 0.0
    ]
    losses = [
        abs(t.get("exit_return", 0.0))
        for t in trades
        if t.get("exit_return", 0.0) < 0.0
    ]

    if not losses:
        return None

    return sum(wins) / sum(losses)


def calculate_sharpe_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0
) -> Optional[float]:
    """Calculates Sharpe ratio. Returns None if returns count < 10."""
    if len(returns) < 10:
        return None

    mean_ret = sum(returns) / len(returns)
    variance = sum((r - mean_ret) ** 2 for r in returns) / (len(returns) - 1)
    std_dev = math.sqrt(variance)

    if std_dev == 0.0:
        return 0.0

    return (mean_ret - risk_free_rate) / std_dev


def calculate_sortino_ratio(
    returns: List[float],
    risk_free_rate: float = 0.0
) -> Optional[float]:
    """Calculates Sortino ratio. Returns None if returns count < 10."""
    if len(returns) < 10:
        return None

    mean_ret = sum(returns) / len(returns)
    downside_diffs = [min(0.0, r - risk_free_rate) ** 2 for r in returns]
    downside_variance = sum(downside_diffs) / (len(returns) - 1)
    downside_deviation = math.sqrt(downside_variance)

    if downside_deviation == 0.0:
        return 0.0

    return (mean_ret - risk_free_rate) / downside_deviation
