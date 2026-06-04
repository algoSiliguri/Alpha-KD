from abc import ABC, abstractmethod
from typing import Dict, Any

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
    def on_tick(self, tick, current_state: dict, payload_buffer: memoryview) -> int:
        pass
