from typing import Type, Dict
from .base import BaseStrategy

STRATEGY_REGISTRY: Dict[str, Type[BaseStrategy]] = {}

def register_strategy(name: str):
    def decorator(cls: Type[BaseStrategy]):
        STRATEGY_REGISTRY[name] = cls
        return cls
    return decorator

# Force load to register
from .cci_strategy import CciStrategy  # noqa: E402
register_strategy("CciStrategy")(CciStrategy)
