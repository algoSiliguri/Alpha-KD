"""Optional mixin to add regime detection to any Strategy subclass."""
try:
    from regime_detection.regime_detection import RegimeDetection
    _REGIME_AVAILABLE = True
except (ImportError, Exception):
    _REGIME_AVAILABLE = False


class RegimeMixin:
    def __init__(
        self,
        *args,
        regime_model_type: str = "markov",
        regime_params: dict = None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.current_regime: str = "unavailable"
        if _REGIME_AVAILABLE:
            try:
                self.regime_detector = RegimeDetection(
                    model_type=regime_model_type,
                    params=regime_params or {"k_regimes": 2},
                )
            except Exception:
                self.regime_detector = None
        else:
            self.regime_detector = None

    def detect_regime(self, df) -> str:
        """Fit regime model and cache result on self.current_regime."""
        if self.regime_detector is None:
            self.current_regime = "unavailable"
            return self.current_regime
        try:
            result = self.regime_detector.detect_regime(df)
            self.current_regime = str(result) if result is not None else "unknown"
        except Exception:
            self.current_regime = "unknown"
        return self.current_regime
