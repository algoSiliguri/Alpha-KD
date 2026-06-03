"""Thread-safe global control state for the simulation and dashboard."""
import threading
from typing import Any, Dict

from alpha_kd.risk.breaker import DrawdownBreaker

_lock = threading.Lock()
_state = {
    "mode": "Historical Backtest",
    "action": "pause",
    "loading": False,
}


def get_control() -> Dict[str, Any]:
    """Retrieve a copy of the current global control state."""
    with _lock:
        return _state.copy()


def update_control(data: Dict[str, Any]) -> None:
    """Update control fields and trigger appropriate state changes."""
    with _lock:
        if "mode" in data:
            _state["mode"] = data["mode"]
        if "action" in data:
            action = data["action"]
            _state["action"] = action
            if action == "halt":
                DrawdownBreaker.force_halt_all()
        if "loading" in data:
            _state["loading"] = bool(data["loading"])


def set_loading(loading: bool) -> None:
    """Convenience helper to update only the loading flag."""
    with _lock:
        _state["loading"] = loading
