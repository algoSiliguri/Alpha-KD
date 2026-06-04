"""CLI entrypoint: python -m alpha_kd --state|--backtest"""
import argparse
import json
from pathlib import Path
from alpha_kd.telemetry import TelemetryBuffer


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
        "--telemetry-path", type=Path, default=Path("telemetry.jsonl")
    )
    args = parser.parse_args()

    if args.state:
        buf = TelemetryBuffer(args.telemetry_path)
        records = buf.tail(1)
        if records:
            print(json.dumps(records[0], indent=2))
        else:
            print("No telemetry records found.")

    if args.backtest:
        from alpha_kd.backtest_telemetry import BacktestTelemetry
        from alpha_kd.data_fetcher import YahooFinanceFetcher
        from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime

        symbol = "AAPL"
        fetcher = YahooFinanceFetcher()
        df = fetcher.fetch(symbol, period="5d", interval="1h")
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
            df,
            RsiSmaRegime,
            params,
            telemetry_path=args.telemetry_path,
        )
        bt.run()
        records = bt.buffer.tail(1)
        print(f"Backtest complete: {len(df)} bars")
        if records:
            print(f"Last state: {records[0]}")


if __name__ == "__main__":
    main()
