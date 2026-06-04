from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple


class BaseStrategy(ABC):
    """
    Pure state machine. Zero global state. No allocations on the hot path.
    """

    def __init__(self, strategy_id: int, parameters: Dict[str, Any]):
        self.id = strategy_id
        self.parameters = parameters
        self.status = 0
        self.unrealized_pnl = 0.0

    @abstractmethod
    def on_tick(
        self, tick, current_state: dict, payload_buffer: memoryview
    ) -> int:
        pass


class Strategy(ABC):
    """Unified interface for all Alpha-KD trading strategies (Legacy)."""

    def __init__(self, data, parameters: dict):
        self.data = data
        self.parameters = parameters
        self.get_features()
        self.start_date_backtest = self.data.index[0]
        self.buy = False
        self.sell = False
        self.open_buy_price: Optional[float] = None
        self.open_sell_price: Optional[float] = None
        self.entry_time = None
        self.exit_time = None

    def get_state(self) -> dict:
        """Return a serializable snapshot of strategy state."""
        return {
            "side": "buy" if self.buy else ("sell" if self.sell else "flat"),
            "entry_price": (
                self.open_buy_price
                if self.buy
                else (self.open_sell_price if self.sell else None)
            ),
            "unrealized_pnl": None,
            "signal": 0,
            "timestamp": None,
        }

    @abstractmethod
    def get_features(self) -> None:
        """Compute technical indicators and signal columns on self.data."""
        ...

    @abstractmethod
    def get_entry_signal(  # noqa: E501
        self, time
    ) -> Tuple[int, Any]:
        """Return entry signal (-1, 0, 1) and entry time."""
        ...

    @abstractmethod
    def get_exit_signal(  # noqa: E501
        self, time
    ) -> Tuple[float, Any]:
        """Return position return and exit time if closing."""
        ...
