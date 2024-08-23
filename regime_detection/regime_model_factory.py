# regime_model_factory.py
from markov_switching_model import MarkovSwitchingModel
from hidden_markov_model import HiddenMarkovModel


class RegimeModelFactory:
    @staticmethod
    def create_model(model_type, params):
        if model_type == "markov":
            return MarkovSwitchingModel(params)
        elif model_type == "hmm":
            return HiddenMarkovModel(params)
        else:
            raise ValueError("Unsupported model type. Choose 'markov' or 'hmm'.")
