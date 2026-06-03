class DrawdownBreaker:
    """Hard 10% drawdown circuit breaker."""

    def __init__(self, limit: float = 0.10, initial_value: float = 100000.0):
        self.limit = limit
        self.peak_value = initial_value
        self.is_halted = False

    def update(self, current_value: float) -> bool:
        """Update tracker with current value and return True if halted."""
        if self.is_halted:
            return True
        if current_value > self.peak_value:
            self.peak_value = current_value

        drawdown = 0.0
        if self.peak_value != 0:
            drawdown = (self.peak_value - current_value) / abs(self.peak_value)

        if drawdown >= self.limit:
            self.is_halted = True
        return self.is_halted
