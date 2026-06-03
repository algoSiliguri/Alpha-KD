import weakref


class DrawdownBreaker:
    """Hard 10% drawdown circuit breaker with global halt capability."""

    _instances = weakref.WeakSet()
    _global_halted = False

    def __init__(self, limit: float = 0.10, initial_value: float = 100000.0):
        self.limit = limit
        self.peak_value = initial_value
        self._is_halted = False
        DrawdownBreaker._instances.add(self)

    @property
    def is_halted(self) -> bool:
        """Check if instance or global system is halted."""
        return self._is_halted or DrawdownBreaker._global_halted

    @is_halted.setter
    def is_halted(self, value: bool) -> None:
        """Set instance-level halt state."""
        self._is_halted = value

    @classmethod
    def force_halt_all(cls) -> None:
        """Trigger global halt across all active and future instances."""
        cls._global_halted = True
        for inst in list(cls._instances):
            inst.is_halted = True

    @classmethod
    def reset_global_halt(cls) -> None:
        """Reset the global halt state."""
        cls._global_halted = False
        for inst in list(cls._instances):
            inst.is_halted = False

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
