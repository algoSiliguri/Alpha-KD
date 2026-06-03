"""Thin adapter: runs per-bar strategy loop and records states."""
import time
from pathlib import Path
from typing import Any, Dict, List, Optional
import pandas as pd

from alpha_kd.risk.breaker import DrawdownBreaker
from alpha_kd.risk.kelly import calculate_kelly_fraction
from alpha_kd.telemetry.logger import TelemetryBuffer


class BacktestTelemetry:
    """Executes per-bar entry/exit logic and persists states."""

    def __init__(
        self,
        data: Any,
        TradingStrategy: Any,
        parameters: Dict[str, Any],
        initial_capital: float = 100_000.0,
        telemetry_path: Optional[Path] = None,
        max_records: int = 10_000,
    ):
        self.capital = initial_capital
        path = telemetry_path or Path("telemetry.jsonl")
        self.buffer = TelemetryBuffer(path, max_records=max_records)
        self.is_multi = isinstance(data, dict)

        if self.is_multi:
            self.strategies = {}
            union_idx = set()
            for sym, df in data.items():
                df_copy = df.copy()
                if df_copy.index.tz is not None:
                    df_copy.index = df_copy.index.tz_convert(None)
                self.strategies[sym] = TradingStrategy(df_copy, parameters)
                union_idx.update(df_copy.index)
            self.timeline = sorted(list(union_idx))
        else:
            df_copy = data.copy()
            if df_copy.index.tz is not None:
                df_copy.index = df_copy.index.tz_convert(None)
            self.strategy = TradingStrategy(df_copy, parameters)
            self.timeline = list(df_copy.index)

    def run(self, delay: float = 0.0) -> None:
        """Execute per-bar loop and record state snapshot."""
        breaker = DrawdownBreaker(limit=0.10, initial_value=self.capital)
        if self.is_multi:
            self._run_multi(breaker, delay)
        else:
            self._run_single(breaker, delay)

    def _run_single(self, breaker: DrawdownBreaker, delay: float) -> None:
        equity = self.capital
        trade_returns = []
        for current_time in self.timeline:
            entry_signal, exit_ret = 0, 0.0
            if not breaker.is_halted:
                entry_signal, _ = self.strategy.get_entry_signal(current_time)
                exit_ret, _ = self.strategy.get_exit_signal(current_time)
                if exit_ret != 0.0:
                    trade_returns.append(exit_ret)
                    equity *= (1.0 + exit_ret)
                    breaker.update(equity)

            k_size = self._calc_kelly(trade_returns) if not breaker.is_halted else 0.0
            state = self.strategy.get_state(current_time)
            state.update({
                "bar_time": str(current_time),
                "entry_signal": entry_signal,
                "exit_return": float(exit_ret),
                "equity": equity,
                "drawdown": (breaker.peak_value - equity) / breaker.peak_value if breaker.peak_value > 0 else 0.0,
                "kelly_size": k_size,
                "is_halted": breaker.is_halted,
            })
            self.buffer.record(state)
            if delay > 0.0:
                time.sleep(delay)

    def _run_multi(self, breaker: DrawdownBreaker, delay: float) -> None:
        symbols = list(self.strategies.keys())
        ticker_equity = {sym: self.capital / len(symbols) for sym in symbols}
        trade_returns = {sym: [] for sym in symbols}
        last_unrealized = {sym: 0.0 for sym in symbols}
        last_state = {sym: {} for sym in symbols}

        for current_time in self.timeline:
            ticker_signals, ticker_exits = {}, {}

            for sym in symbols:
                strat = self.strategies[sym]
                entry_sig, exit_ret = 0, 0.0
                if current_time in strat.data.index:
                    if not breaker.is_halted:
                        entry_sig, _ = strat.get_entry_signal(current_time)
                        exit_ret, _ = strat.get_exit_signal(current_time)
                        if exit_ret != 0.0:
                            trade_returns[sym].append(exit_ret)
                            ticker_equity[sym] *= (1.0 + exit_ret)
                    s_state = strat.get_state(current_time)
                    last_unrealized[sym] = s_state.get("unrealized_pnl") or 0.0
                    last_state[sym] = s_state
                ticker_signals[sym] = entry_sig
                ticker_exits[sym] = exit_ret

            agg_equity = sum(ticker_equity[sym] * (1.0 + last_unrealized[sym]) for sym in symbols)
            breaker.update(agg_equity)

            tickers_telemetry = {}
            for sym in symbols:
                k_size = self._calc_kelly(trade_returns[sym]) if not breaker.is_halted else 0.0
                state_copy = last_state[sym].copy()
                state_copy.update({
                    "entry_signal": ticker_signals[sym],
                    "exit_return": float(ticker_exits[sym]),
                    "kelly_size": k_size,
                    "equity": ticker_equity[sym],
                })
                tickers_telemetry[sym] = state_copy

            agg_drawdown = (breaker.peak_value - agg_equity) / breaker.peak_value if breaker.peak_value > 0 else 0.0
            self.buffer.record({
                "bar_time": str(current_time),
                "timestamp": str(current_time),
                "equity": agg_equity,
                "drawdown": agg_drawdown,
                "is_halted": breaker.is_halted,
                "tickers": tickers_telemetry,
            })
            if delay > 0.0:
                time.sleep(delay)

    def _calc_kelly(self, returns: List[float]) -> float:
        pos = [r for r in returns if r > 0]
        neg = [r for r in returns if r < 0]
        if not returns:
            return 0.1
        p = len(pos) / len(returns)
        b = (sum(pos)/len(pos)) / abs(sum(neg)/len(neg)) if pos and neg else 1.5
        return calculate_kelly_fraction(p=p, b=b, f_s=0.5)

