# hidden_markov_model.py
import pandas as pd
from hmmlearn.hmm import GaussianHMM
from regime_model import RegimeModel


class HiddenMarkovModel(RegimeModel):
    def __init__(self, params):
        self.model = GaussianHMM(
            n_components=params.get("n_components", 2),
            covariance_type=params.get("covariance_type", "full"),
            n_iter=params.get("n_iter", 100),
        )

    def fit(self, df, params):
        data = df[params.get("features")].values
        self.model.fit(data)
        return self.model
