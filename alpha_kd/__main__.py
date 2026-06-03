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


def run_simulation(path: Path):
    """Background simulator writing mock ticks and risk to logs."""
    buf = TelemetryBuffer(path)
    breaker = DrawdownBreaker(limit=0.10, initial_value=100000.0)
    equity = 100000.0
    side = "flat"
    entry_price = 0.0

    if path.exists():
        try:
            path.unlink()
        except Exception:
            pass

    while True:
        ret = random.uniform(-0.015, 0.012) if side != "flat" else 0.0
        if side == "flat":
            if random.random() < 0.20 and not breaker.is_halted:
                side = random.choice(["buy", "sell"])
                entry_price = 100.0 + random.uniform(-5.0, 5.0)
        else:
            if random.random() < 0.30 or breaker.is_halted:
                side = "flat"
                entry_price = 0.0

        if side != "flat":
            pos_ret = ret if side == "buy" else -ret
            equity *= (1.0 + pos_ret)
            breaker.update(equity)

        p = 0.55 + random.uniform(-0.05, 0.05)
        b = 1.5 + random.uniform(-0.2, 0.2)
        kelly_size = (
            calculate_kelly_fraction(p=p, b=b, f_s=0.5)
            if not breaker.is_halted
            else 0.0
        )

        now_str = datetime.datetime.now().strftime("%H:%M:%S")
        state = {
            "side": side,
            "entry_price": entry_price if side != "flat" else None,
            "unrealized_pnl": ret if side != "flat" else None,
            "signal": 1 if side == "buy" else (-1 if side == "sell" else 0),
            "timestamp": now_str,
            "bar_time": now_str,
            "equity": equity,
            "drawdown": (
                (breaker.peak_value - equity) / breaker.peak_value
                if breaker.peak_value > 0
                else 0.0
            ),
            "kelly_size": kelly_size,
            "is_halted": breaker.is_halted,
        }
        buf.record(state)
        time.sleep(1.0)


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
    args = parser.parse_args()

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

    elif args.dashboard:
        from alpha_kd.dashboard.server import start_dashboard

        t = threading.Thread(
            target=run_simulation,
            args=(args.telemetry_path,),
            daemon=True,
        )
        t.start()
        start_dashboard(port=8080)


if __name__ == "__main__":
    main()
