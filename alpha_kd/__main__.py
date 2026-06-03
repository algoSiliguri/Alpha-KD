"""CLI entrypoint: python -m alpha_kd --state|--backtest|--dashboard"""
import argparse
import json
import threading
import time
from pathlib import Path

from alpha_kd.telemetry.logger import TelemetryBuffer


def run_simulation(path: Path, symbols: list):
    """Background simulator running dynamic execution horizons."""
    from alpha_kd.dashboard.control_state import get_control
    from alpha_kd.data.loader import init_horizon_telemetry

    current_mode = None
    bt = None
    timeline_idx = 0

    while True:
        ctrl = get_control()
        action = ctrl["action"]
        mode = ctrl["mode"]

        if mode != current_mode:
            try:
                bt = init_horizon_telemetry(mode, symbols, path)
                current_mode = mode
                timeline_idx = 0
            except Exception as e:
                print(f"Error loading telemetry for mode {mode}: {e}")
                time.sleep(1.0)
                continue

        if action == "pause":
            time.sleep(0.1)
            continue
        elif action == "halt":
            time.sleep(0.5)
            continue

        if bt and timeline_idx < len(bt.timeline):
            current_time = bt.timeline[timeline_idx]
            bt.step_one(current_time)
            timeline_idx += 1

            if mode == "Paper Trading (Real-Time Live)":
                delay = 2.0
            elif mode == "Forward Test (Simulated Live)":
                delay = 0.5
            else:
                delay = 0.05
            time.sleep(delay)
        else:
            time.sleep(0.1)


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
    symbols = (
        [s.strip() for s in args.symbols.split(",") if s.strip()]
        if args.symbols
        else TARGET_SYMBOLS
    )

    if args.state:
        buf = TelemetryBuffer(args.telemetry_path)
        records = buf.tail(1)
        print(
            json.dumps(records[0], indent=2)
            if records
            else "No telemetry records found."
        )

    elif args.backtest:
        from alpha_kd.data.loader import init_horizon_telemetry

        bt = init_horizon_telemetry(
            "Forward Test (Simulated Live)", symbols, args.telemetry_path
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
