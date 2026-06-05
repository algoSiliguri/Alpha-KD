#!/usr/bin/env python3
import os
import sys
import uuid
import signal
import time
import argparse
import multiprocessing.shared_memory as shm
import gc
import ctypes
import subprocess

from alpha_kd.execution.datafeed import HistoricalFeed
from alpha_kd.execution.engine import ExecutionEngine
from alpha_kd.strategies.cci_strategy import CciStrategy
from alpha_kd.telemetry.structures import DoubleBufferedSnapshot


def cleanup(signum, frame):
    print("\n[Orchestrator] Caught SIGINT. Performing clean shutdown...")
    try:
        session_id = os.environ.get("ALPHA_KD_SESSION_ID", "")
        if session_id:
            for name in [f"ring_{session_id}", f"snap_{session_id}"]:
                try:
                    memory = shm.SharedMemory(name=name)
                    memory.close()
                    memory.unlink()
                except FileNotFoundError:
                    pass
    except Exception as e:
        print(f"[Orchestrator] Error during shared memory cleanup: {e}")
    sys.exit(0)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--session-id", default=str(uuid.uuid4()))
    parser.add_argument("--data-feed", required=True)
    parser.add_argument(
        "--tick-rate",
        type=int,
        default=50,
        help="Ticks per second throttle (default: 50)"
    )
    args = parser.parse_args()

    session_id = args.session_id
    os.environ["ALPHA_KD_SESSION_ID"] = session_id
    print(f"[Orchestrator] Starting Alpha-KD with Session ID: {session_id}")

    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)

    # Clean slate and allocate memory
    ring_name = f"ring_{session_id}"
    snap_name = f"snap_{session_id}"

    # 10MB ring buffer
    ring_size = 10 * 1024 * 1024
    snap_size = ctypes.sizeof(DoubleBufferedSnapshot)

    for name in [ring_name, snap_name]:
        try:
            m = shm.SharedMemory(name=name)
            m.unlink()
        except FileNotFoundError:
            pass

    ring_shm = shm.SharedMemory(name=ring_name, create=True, size=ring_size)
    snap_shm = shm.SharedMemory(name=snap_name, create=True, size=snap_size)

    # Spawn FastAPI UI Process
    print("[Orchestrator] Spawning FastAPI Web UI backend process...")
    ui_process = subprocess.Popen([
        sys.executable,
        "-m",
        "alpha_kd.ui.backend",
        "--session-id",
        session_id,
        "--port",
        "8000"
    ])

    # Let the backend server start
    time.sleep(1.0)

    # Init Engine
    feed = HistoricalFeed(args.data_feed)
    strategies = [CciStrategy(1, {"cci_period": 20, "atr_period": 20})]

    engine = ExecutionEngine(
        strategies=strategies,
        data_feed=feed,
        ipc_pipe_fd=None,
        ring_mmap=ring_shm.buf,
        snap_mmap=snap_shm.buf,
        tick_rate=args.tick_rate
    )

    # Disable GC to prove zero-slop
    gc.disable()
    print(
        f"[Orchestrator] GC Disabled. Firing hot loop at tick rate: "
        f"{args.tick_rate if args.tick_rate else 'MAX'}..."
    )
    t0 = time.perf_counter()
    engine.run_loop()
    t1 = time.perf_counter()

    print(
        f"[Orchestrator] Run complete in {t1-t0:.4f}s. "
        f"Processed {engine.tick_sequence} ticks."
    )
    print(
        f"[Orchestrator] Throughput: "
        f"{engine.tick_sequence / (t1-t0):.0f} ticks/sec"
    )

    print("\n[Orchestrator] === ENGINE_DONE ===")
    print("[Orchestrator] Telemetry loop closed. UI server remains active.")
    print("[Orchestrator] Press Ctrl+C to execute clean-slate teardown.")

    try:
        ui_process.wait()
    except KeyboardInterrupt:
        pass

    cleanup(None, None)


if __name__ == "__main__":
    main()
