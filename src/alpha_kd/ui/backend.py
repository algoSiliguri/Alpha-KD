import argparse
import asyncio
import ctypes
import json
import multiprocessing.shared_memory as shm
import tempfile
from pathlib import Path
from fastapi import FastAPI, WebSocket, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from alpha_kd.telemetry.structures import TelemetryHeader, DoubleBufferedSnapshot
from alpha_kd.telemetry.seqlock import SeqLock
from alpha_kd.data_fetcher import YahooFinanceFetcher
from alpha_kd.backtest_telemetry import BacktestTelemetry
from alpha_kd.strategies.rsi_sma import RsiSma
from alpha_kd.strategies.rsi_sma_regime import RsiSmaRegime
from alpha_kd.metrics import (
    reconstruct_equity_curve,
    calculate_cumulative_returns,
    calculate_max_drawdown,
    calculate_drawdown_duration,
    reconstruct_trades,
    calculate_win_rate,
    calculate_profit_factor,
    calculate_sharpe_ratio,
    calculate_sortino_ratio,
)

app = FastAPI(title="Alpha-KD Telemetry Server")

# Allow CORS for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global variables for shared memory
ring_shm = None
snap_shm = None
snapshot_mem = None
header_size = ctypes.sizeof(TelemetryHeader)

DEFAULT_PARAMS = {
    "fast_sma": 10,
    "slow_sma": 20,
    "rsi": 14,
    "tp": 0.01,
    "sl": -0.01,
    "cost": 0.0001,
    "leverage": 1,
}


def read_frame_at_offset(buf, offset):
    header = TelemetryHeader.from_buffer(buf, offset)

    def get_data():
        return {
            "seqlock": header.seqlock,
            "timestamp_ns": header.timestamp_ns,
            "strategy_id": header.strategy_id,
            "status_flag": header.status_flag,
            "current_price": header.current_price,
            "position_size": header.position_size,
            "unrealized_pnl": header.unrealized_pnl,
            "realized_pnl": header.realized_pnl,
            "allocated_capital": header.allocated_capital,
            "payload_length": header.payload_length,
        }

    return SeqLock.read_retry(header, get_data, field_name="seqlock")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/strategies")
def get_strategies():
    return {
        "strategies": [
            {
                "strategy_id": "rsi_sma",
                "strategy_name": "RsiSma",
                "path": "legacy",
                "status": "research_only",
                "parameters": DEFAULT_PARAMS,
                "regime_aware": False,
                "has_real_data": True,
            },
            {
                "strategy_id": "rsi_sma_regime",
                "strategy_name": "RsiSmaRegime",
                "path": "legacy",
                "status": "research_only",
                "parameters": DEFAULT_PARAMS,
                "regime_aware": True,
                "has_real_data": True,
            },
            {
                "strategy_id": "cci",
                "strategy_name": "CciStrategy",
                "path": "zero_alloc",
                "status": "stub",
                "parameters": {"cci_period": 20, "atr_period": 20},
                "regime_aware": False,
                "has_real_data": False,
            },
        ]
    }


@app.get("/api/backtest/{strategy_id}")
def run_backtest(
    strategy_id: str,
    symbol: str = "AAPL",
    period: str = "5d",
    interval: str = "1h",
):
    if strategy_id == "cci":
        return {
            "strategy_id": "cci",
            "symbol": symbol,
            "period": period,
            "interval": interval,
            "bars_processed": 0,
            "equity_curve": [],
            "cumulative_returns": [],
            "per_bar": [],
            "trades": [],
            "metrics": None,
            "regime_timeline": [],
            "forward_test": None,
        }

    if strategy_id not in ("rsi_sma", "rsi_sma_regime"):
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_id}' not found"
        )

    try:
        fetcher = YahooFinanceFetcher()
        df = fetcher.fetch(symbol, period=period, interval=interval)
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to fetch market data for symbol '{symbol}': {e}",
        )

    strat_class = RsiSma if strategy_id == "rsi_sma" else RsiSmaRegime

    with tempfile.TemporaryDirectory() as tmpdir:
        tel_path = Path(tmpdir) / "telemetry.jsonl"
        bt = BacktestTelemetry(
            df, strat_class, DEFAULT_PARAMS, telemetry_path=tel_path
        )
        bt.run()

        records = []
        if tel_path.exists():
            with open(tel_path, "r") as f:
                for line in f:
                    if line.strip():
                        records.append(json.loads(line))

    equity_curve = reconstruct_equity_curve(records)
    cum_returns = calculate_cumulative_returns(equity_curve)
    max_dd = calculate_max_drawdown(equity_curve)
    dd_dur = calculate_drawdown_duration(equity_curve)
    trades = reconstruct_trades(records)
    win_rate = calculate_win_rate(trades)
    profit_factor = calculate_profit_factor(trades)

    exit_returns = [t["exit_return"] for t in trades if "exit_return" in t]
    sharpe = calculate_sharpe_ratio(exit_returns)
    sortino = calculate_sortino_ratio(exit_returns)

    avg_duration = (
        sum(t["duration_bars"] for t in trades) / len(trades)
        if trades
        else 0.0
    )

    return {
        "strategy_id": strategy_id,
        "symbol": symbol,
        "period": period,
        "interval": interval,
        "bars_processed": len(records),
        "equity_curve": equity_curve,
        "cumulative_returns": cum_returns,
        "per_bar": records,
        "trades": trades,
        "metrics": {
            "total_return": cum_returns[-1] if cum_returns else 0.0,
            "sharpe_ratio": sharpe,
            "max_drawdown": max_dd,
            "drawdown_duration_bars": dd_dur,
            "num_trades": len(trades),
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_trade_duration_bars": avg_duration,
            "sortino_ratio": sortino,
        },
        "regime_timeline": [r.get("regime", "unknown") for r in records],
        "forward_test": None,
    }


@app.get("/api/telemetry/history")
def get_telemetry_history(n: int = 100):
    from alpha_kd.telemetry import TelemetryBuffer

    buffer = TelemetryBuffer(Path("telemetry.jsonl"))
    records = buffer.tail(n)
    return {"records": records, "total_records": len(records)}


@app.get("/api/telemetry/snapshot")
def get_snapshot():
    if snapshot_mem is None:
        return {"status": "error", "message": "Shared memory not connected"}

    def _read_snap():
        idx = snapshot_mem.active_index
        buf = snapshot_mem.buffers[idx]
        return {
            "sequence_id": buf.sequence_id,
            "is_active": buf.is_active,
            "unrealized_pnl": buf.unrealized_pnl,
            "allocated_capital": buf.allocated_capital,
        }

    try:
        data = SeqLock.read_retry(
            snapshot_mem, _read_snap, field_name="seqlock"
        )
        return {"status": "success", "snapshot": data}
    except TimeoutError:
        return {"status": "error", "message": "SeqLock timeout"}


@app.websocket("/api/telemetry/ws")
async def websocket_telemetry(websocket: WebSocket):
    await websocket.accept()
    if ring_shm is None:
        await websocket.close(
            code=1008,
            reason="Shared memory not initialized"
        )
        return

    buf = ring_shm.buf
    offset = 0
    buffer_len = len(buf)

    try:
        while True:
            if offset + header_size > buffer_len:
                offset = 0

            try:
                frame = read_frame_at_offset(buf, offset)
                seqlock = frame["seqlock"]

                if seqlock == 0:
                    await asyncio.sleep(0.01)
                    continue

                if frame["status_flag"] == 0xFF:
                    offset = 0
                    continue

                payload_len = frame["payload_length"]
                frame_size = header_size + payload_len

                if offset + frame_size > buffer_len:
                    offset = 0
                    continue

                # Slice the binary segment and send
                raw_data = bytes(buf[offset : offset + frame_size])
                await websocket.send_bytes(raw_data)
                offset += frame_size

            except TimeoutError:
                await asyncio.sleep(0.001)
                continue

    except Exception:
        pass  # Socket disconnected


def main():
    import uvicorn

    parser = argparse.ArgumentParser(description="Alpha-KD Web UI Backend")
    parser.add_argument(
        "--session-id", required=True, help="Shared memory session ID"
    )
    parser.add_argument(
        "--host", default="127.0.0.1", help="Uvicorn bind host"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Uvicorn bind port"
    )
    args = parser.parse_args()

    global ring_shm, snap_shm, snapshot_mem
    try:
        ring_shm = shm.SharedMemory(name=f"ring_{args.session_id}")
        snap_shm = shm.SharedMemory(name=f"snap_{args.session_id}")
        snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap_shm.buf)
    except Exception as e:
        print(
            f"Error: Failed to attach to shared memory session "
            f"'{args.session_id}': {e}"
        )
        return

    print(
        f"Starting server for session '{args.session_id}' "
        f"on {args.host}:{args.port}"
    )
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()
