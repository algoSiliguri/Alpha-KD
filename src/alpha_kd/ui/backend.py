import argparse
import asyncio
import ctypes
import multiprocessing.shared_memory as shm
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from alpha_kd.telemetry.structures import TelemetryHeader, DoubleBufferedSnapshot
from alpha_kd.telemetry.seqlock import SeqLock

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
