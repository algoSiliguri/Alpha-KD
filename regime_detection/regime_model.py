# regime_model.py
from abc import ABC, abstractmethod


class RegimeModel(ABC):
    @abstractmethod
    def fit(self, df, params):
        pass
