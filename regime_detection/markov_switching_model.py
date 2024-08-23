# markov_switching_model.py
import pandas as pd
from statsmodels.tsa.regime_switching.markov_regression import MarkovRegression
from regime_model import RegimeModel


class MarkovSwitchingModel(RegimeModel):
    def __init__(self, params):
        self.model = MarkovRegression(
            endog=params.get("endog"),
            k_regimes=params.get("k_regimes", 2),
            trend=params.get("trend", "c"),
            switching_variance=params.get("switching_variance", True),
        )

    def fit(self, df, params):
        return self.model.fit()
