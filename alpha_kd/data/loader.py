"""Loader utility to fetch ticker data and initialize telemetry."""
from pathlib import Path

from alpha_kd.data.data_fetcher import YahooFinanceFetcher
from alpha_kd.dashboard.control_state import set_loading
from alpha_kd.strategy.rsi_sma_regime import RsiSmaRegime
from alpha_kd.telemetry.backtest import BacktestTelemetry


def init_horizon_telemetry(
    mode: str, symbols: list, path: Path
) -> BacktestTelemetry:
    """Fetch ticker data for the given mode and return telemetry instance."""
    set_loading(True)
    try:
        if mode == "Forward Test (Simulated Live)":
            period, interval = "5d", "1h"
        elif mode == "Paper Trading (Real-Time Live)":
            period, interval = "1d", "1h"
        else:
            period, interval = "1mo", "1h"

        fetcher = YahooFinanceFetcher()
        dfs = {
            sym: fetcher.fetch(sym, period=period, interval=interval)
            for sym in symbols
        }

        params = {
            "fast_sma": 10,
            "slow_sma": 20,
            "rsi": 14,
            "tp": 0.01,
            "sl": -0.01,
            "cost": 0.0001,
            "leverage": 1,
        }

        if path.exists():
            try:
                path.unlink()
            except Exception:
                pass

        return BacktestTelemetry(dfs, RsiSmaRegime, params, telemetry_path=path)
    finally:
        set_loading(False)
