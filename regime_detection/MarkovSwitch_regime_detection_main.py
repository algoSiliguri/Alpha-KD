from regime_detection import RegimeDetection

# Example usage
params = {"endog": some_data, "k_regimes": 3}
regime_detector = RegimeDetection("markov", params)
markov_model = regime_detector.detect_regime(df, params)
