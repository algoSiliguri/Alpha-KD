from abc import ABC, abstractmethod
from typing import Optional, Tuple

import pandas as pd


class Strategy(ABC):
    """Unified interface for all Alpha-KD trading strategies."""

    def __init__(self, data: pd.DataFrame, parameters: dict):
        self.data = data
        self.parameters = parameters
        self.get_features()
        self.start_date_backtest = self.data.index[0]
        self.buy = False
        self.sell = False
        self.open_buy_price: Optional[float] = None
        self.open_sell_price: Optional[float] = None
        self.entry_time: Optional[pd.Timestamp] = None
        self.exit_time: Optional[pd.Timestamp] = None

    @abstractmethod
    def get_features(self) -> None:
        """Compute technical indicators and signal columns on self.data."""
        ...

    @abstractmethod
    def get_entry_signal(self, time: pd.Timestamp) -> Tuple[int, Optional[pd.Timestamp]]:
        """Return entry signal (-1, 0, 1) and entry time."""
        ...

    @abstractmethod
    def get_exit_signal(self, time: pd.Timestamp) -> Tuple[float, Optional[pd.Timestamp]]:
        """Return position return and exit time if closing."""
        ...
