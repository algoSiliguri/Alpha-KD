"""Thin adapter: runs per-bar strategy loop and records get_state() snapshots."""
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd

from alpha_kd.telemetry import TelemetryBuffer


class BacktestTelemetry:
    """Executes per-bar entry/exit logic and persists strategy.get_state() at every bar.

    Works with any alpha_kd Strategy subclass (2-arg constructor: data, parameters).
    Does not wrap Quantreo.Backtest — that class uses a 3-arg strategy constructor
    incompatible with alpha_kd.strategies.base.Strategy.
    """

    def __init__(
        self,
        data: pd.DataFrame,
        TradingStrategy: Any,
        parameters: Dict[str, Any],
        initial_capital: int = 100_000,
        telemetry_path: Optional[Path] = None,
        max_records: int = 10_000,
    ):
        self.strategy = TradingStrategy(data, parameters)
        path = telemetry_path or Path("telemetry.jsonl")
        self.buffer = TelemetryBuffer(path, max_records=max_records)

    def run(self) -> None:
        """Execute per-bar loop and record state snapshot after every bar."""
        for current_time in self.strategy.data.index:
            entry_signal, _ = self.strategy.get_entry_signal(current_time)
            exit_ret, _ = self.strategy.get_exit_signal(current_time)
            state = self.strategy.get_state()
            state["bar_time"] = str(current_time)
            state["entry_signal"] = entry_signal
            state["exit_return"] = float(exit_ret) if exit_ret else 0.0
            self.buffer.record(state)
