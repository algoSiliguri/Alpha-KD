# regime_detection.py
from regime_model_factory import RegimeModelFactory


class RegimeDetection:
    def __init__(self, model_type, params):
        self.model = RegimeModelFactory.create_model(model_type, params)

    def detect_regime(self, df, params):
        return self.model.fit(df, params)
