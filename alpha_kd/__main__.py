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
    parser.add_argument("--telemetry-path", type=Path, default=Path("telemetry.jsonl"))
    args = parser.parse_args()

    if args.state:
        buf = TelemetryBuffer(args.telemetry_path)
        records = buf.tail(1)
        if records:
            print(json.dumps(records[0], indent=2))
        else:
            print("No telemetry records found.")

    if args.backtest:
        print("Backtest telemetry mode — not yet wired to live data.")
        print("Use BacktestTelemetry(adapter) in scripts for now.")


if __name__ == "__main__":
    main()
