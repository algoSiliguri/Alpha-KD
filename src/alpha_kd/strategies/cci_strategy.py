import numpy as np
from alpha_kd.strategies.base import BaseStrategy

class CciStrategy(BaseStrategy):
    def __init__(self, strategy_id: int, parameters: dict):
        super().__init__(strategy_id, parameters)
        self.cci_period = parameters.get("cci_period", 20)
        self.atr_period = parameters.get("atr_period", 20)

        # Circular buffers for pure numpy zero-allocation execution
        self._price_buffer = np.zeros(
            max(self.cci_period, self.atr_period), dtype=np.float32
        )
        self._buffer_idx = 0
        self._is_filled = False

    def on_tick(self, tick, current_state: dict, payload_buffer: memoryview) -> int:
        # Update circular buffer (zero-allocation)
        idx = self._buffer_idx % len(self._price_buffer)
        self._price_buffer[idx] = tick.close

        self._buffer_idx += 1
        if self._buffer_idx >= len(self._price_buffer):
            self._is_filled = True

        return 0 # Zero payload bytes written
