"""RSI+SMA strategy with HMM regime detection."""
import pandas as pd
from hmmlearn.hmm import GaussianHMM

from alpha_kd.strategy.rsi_sma import RsiSma


class RsiSmaRegime(RsiSma):
    """Extends RsiSma with a 3-state HMM regime label."""

    def __init__(self, data: pd.DataFrame, parameters: dict):
        super().__init__(data, parameters)
        self.regime_label: str = "unknown"
        self._fit_regime()

    def _fit_regime(self) -> None:
        """Fit 3-state HMM on log-returns and label last bar."""
        returns = self.data["close"].pct_change().dropna().values.reshape(-1, 1)
        if len(returns) < 30:
            self.regime_label = "unknown"
            return
        try:
            model = GaussianHMM(
                n_components=3,
                covariance_type="diag",
                n_iter=100,
                random_state=42,
            )
            model.fit(returns)
            means = model.means_.flatten()
            order = means.argsort()
            last_state = model.predict(returns)[-1]
            label_map = {
                order[0]: "bear",
                order[1]: "sideways",
                order[2]: "bull",
            }
            self.regime_label = label_map.get(last_state, "unknown")
        except Exception:
            self.regime_label = "unknown"

    def get_state(self) -> dict:
        state = super().get_state()
        state["regime"] = self.regime_label
        return state
