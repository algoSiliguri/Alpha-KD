"""Thin adapter: runs per-bar strategy loop and records states."""
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from alpha_kd.risk.breaker import DrawdownBreaker
from alpha_kd.risk.kelly import calculate_kelly_fraction
from alpha_kd.telemetry.logger import TelemetryBuffer


class BacktestTelemetry:
    """Executes per-bar entry/exit logic and persists states."""

    def __init__(
        self,
        data: pd.DataFrame,
        TradingStrategy: Any,
        parameters: Dict[str, Any],
        initial_capital: float = 100_000.0,
        telemetry_path: Optional[Path] = None,
        max_records: int = 10_000,
    ):
        self.strategy = TradingStrategy(data, parameters)
        self.capital = initial_capital
        path = telemetry_path or Path("telemetry.jsonl")
        self.buffer = TelemetryBuffer(path, max_records=max_records)

    def run(self) -> None:
        """Execute per-bar loop and record state snapshot."""
        breaker = DrawdownBreaker(limit=0.10, initial_value=self.capital)
        equity = self.capital

        for current_time in self.strategy.data.index:
            if breaker.is_halted:
                entry_signal = 0
                exit_ret = 0.0
            else:
                entry_signal, _ = self.strategy.get_entry_signal(current_time)
                exit_ret, _ = self.strategy.get_exit_signal(current_time)
                if exit_ret != 0.0:
                    equity *= (1.0 + exit_ret)
                    breaker.update(equity)

            # Sizing calculation based on historical stats:
            # p = 0.55, win/loss = 1.5, scale = 0.5 (half-kelly)
            # f* = 0.5 * (0.55 - 0.45 / 1.5) = 0.125
            kelly_size = (
                calculate_kelly_fraction(p=0.55, b=1.5, f_s=0.5)
                if not breaker.is_halted
                else 0.0
            )

            state = self.strategy.get_state()
            state["bar_time"] = str(current_time)
            state["entry_signal"] = entry_signal
            state["exit_return"] = float(exit_ret) if exit_ret else 0.0
            state["equity"] = equity
            peak = breaker.peak_value
            state["drawdown"] = (
                (peak - equity) / peak if peak > 0 else 0.0
            )
            state["kelly_size"] = kelly_size
            state["is_halted"] = breaker.is_halted
            self.buffer.record(state)
