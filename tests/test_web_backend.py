import ctypes
import gc
import multiprocessing.shared_memory as shm
import pytest
from fastapi.testclient import TestClient
from alpha_kd.telemetry.structures import (
    TelemetryHeader,
    DoubleBufferedSnapshot,
)
from alpha_kd.telemetry.seqlock import SeqLock
from alpha_kd.ui.backend import app
import alpha_kd.ui.backend as backend


@pytest.fixture
def mock_shm():
    # Setup dummy shared memory segments
    ring_size = ctypes.sizeof(TelemetryHeader) * 10
    snap_size = ctypes.sizeof(DoubleBufferedSnapshot)

    ring = shm.SharedMemory(create=True, size=ring_size)
    snap = shm.SharedMemory(create=True, size=snap_size)

    # Initialize segments to zero using ctypes casting
    (ctypes.c_char * ring_size).from_buffer(ring.buf)[:] = b"\x00" * ring_size
    (ctypes.c_char * snap_size).from_buffer(snap.buf)[:] = b"\x00" * snap_size

    yield ring, snap

    # Clear references to prevent exported pointer BufferError
    backend.ring_shm = None
    backend.snap_shm = None
    backend.snapshot_mem = None
    gc.collect()

    # Cleanup
    ring.close()
    ring.unlink()
    snap.close()
    snap.unlink()


def test_health_check():
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_snapshot_endpoint(mock_shm):
    ring, snap = mock_shm

    # Map snapshot struct and write mock state
    snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap.buf)
    with SeqLock.write_lock(snapshot_mem, "seqlock"):
        snapshot_mem.active_index = 0
        buf = snapshot_mem.buffers[0]
        buf.sequence_id = 42
        buf.is_active = True
        buf.unrealized_pnl = 150.5
        buf.allocated_capital = 5000.0

    # Inject mock shared memory references into backend
    backend.ring_shm = ring
    backend.snap_shm = snap
    backend.snapshot_mem = snapshot_mem

    client = TestClient(app)
    response = client.get("/api/telemetry/snapshot")
    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["snapshot"]["sequence_id"] == 42
    assert res_data["snapshot"]["unrealized_pnl"] == pytest.approx(150.5)
    assert res_data["snapshot"]["allocated_capital"] == pytest.approx(5000.0)


def test_websocket_streaming(mock_shm):
    ring, snap = mock_shm
    snapshot_mem = DoubleBufferedSnapshot.from_buffer(snap.buf)

    # Write a dummy tick structure into the ring buffer
    header = TelemetryHeader.from_buffer(ring.buf, 0)
    with SeqLock.write_lock(header, "seqlock"):
        header.timestamp_ns = 123456789
        header.strategy_id = 1
        header.status_flag = 2
        header.current_price = 1.05
        header.position_size = 100.0
        header.unrealized_pnl = 15.0
        header.realized_pnl = 5.0
        header.allocated_capital = 1000.0
        header.payload_length = 0

    backend.ring_shm = ring
    backend.snap_shm = snap
    backend.snapshot_mem = snapshot_mem

    client = TestClient(app)
    with client.websocket_connect("/api/telemetry/ws") as websocket:
        # Receive binary payload
        data = websocket.receive_bytes()
        assert len(data) == ctypes.sizeof(TelemetryHeader)

        # Deserialize and verify
        received_header = TelemetryHeader.from_buffer_copy(data)
        assert received_header.timestamp_ns == 123456789
        assert received_header.strategy_id == 1
        assert received_header.status_flag == 2
        assert received_header.current_price == pytest.approx(1.05)
