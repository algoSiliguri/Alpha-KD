"""CLI entrypoint: python -m alpha_kd --state|--backtest|--dashboard"""
import argparse
import datetime
import json
import random
import threading
import time
from pathlib import Path

from alpha_kd.risk.breaker import DrawdownBreaker
from alpha_kd.risk.kelly import calculate_kelly_fraction
from alpha_kd.telemetry.logger import TelemetryBuffer


def run_simulation(path: Path, symbols: list):
    """Background simulator running real historical backtest replay."""
    from alpha_kd.data.data_fetcher import YahooFinanceFetcher
    from alpha_kd.strategy.rsi_sma_regime import RsiSmaRegime
    from alpha_kd.telemetry.backtest import BacktestTelemetry

    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass

    fetcher = YahooFinanceFetcher()
    dfs = {sym: fetcher.fetch(sym, period="1mo", interval="1h") for sym in symbols}
    params = {
        "fast_sma": 10,
        "slow_sma": 20,
        "rsi": 14,
        "tp": 0.01,
        "sl": -0.01,
        "cost": 0.0001,
        "leverage": 1,
    }
    bt = BacktestTelemetry(dfs, RsiSmaRegime, params, telemetry_path=path)
    bt.run(delay=1.0)


def main():
    parser = argparse.ArgumentParser(description="Alpha-KD CLI")
    parser.add_argument(
        "--state", action="store_true", help="Print latest telemetry entry"
    )
    parser.add_argument(
        "--backtest",
        action="store_true",
        help="Run a minimal backtest and print telemetry summary",
    )
    parser.add_argument(
        "--dashboard", action="store_true", help="Start telemetry dashboard"
    )
    parser.add_argument(
        "--telemetry-path",
        type=Path,
        default=Path("telemetry.jsonl"),
    )
    parser.add_argument(
        "--symbols",
        type=str,
        default=None,
        help="Comma-separated list of target symbols",
    )
    args = parser.parse_args()

    from alpha_kd.config.config import TARGET_SYMBOLS
    if args.symbols:
        symbols = [s.strip() for s in args.symbols.split(",") if s.strip()]
    else:
        symbols = TARGET_SYMBOLS

    if args.state:
        buf = TelemetryBuffer(args.telemetry_path)
        records = buf.tail(1)
        print(
            json.dumps(records[0], indent=2)
            if records
            else "No telemetry records found."
        )

    elif args.backtest:
        from alpha_kd.data.data_fetcher import YahooFinanceFetcher
        from alpha_kd.strategy.rsi_sma_regime import RsiSmaRegime
        from alpha_kd.telemetry.backtest import BacktestTelemetry

        fetcher = YahooFinanceFetcher()
        dfs = {sym: fetcher.fetch(sym, period="5d", interval="1h") for sym in symbols}
        params = {
            "fast_sma": 10,
            "slow_sma": 20,
            "rsi": 14,
            "tp": 0.01,
            "sl": -0.01,
            "cost": 0.0001,
            "leverage": 1,
        }
        bt = BacktestTelemetry(
            dfs,
            RsiSmaRegime,
            params,
            telemetry_path=args.telemetry_path,
        )
        bt.run()
        records = bt.buffer.tail(1)
        print(f"Backtest complete: {len(symbols)} symbols, {len(bt.timeline)} bars")
        if records:
            print(f"Last state: {records[0]}")

    elif args.dashboard:
        from alpha_kd.dashboard.server import start_dashboard

        t = threading.Thread(
            target=run_simulation,
            args=(args.telemetry_path, symbols),
            daemon=True,
        )
        t.start()
        start_dashboard(port=8080)


if __name__ == "__main__":
    main()
