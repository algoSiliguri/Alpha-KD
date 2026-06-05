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


def test_get_strategies_endpoint():
    client = TestClient(app)
    response = client.get("/api/strategies")
    assert response.status_code == 200
    data = response.json()
    assert "strategies" in data
    strategies = data["strategies"]
    assert len(strategies) == 3
    ids = [s["strategy_id"] for s in strategies]
    assert "rsi_sma" in ids
    assert "rsi_sma_regime" in ids
    assert "cci" in ids


def test_run_backtest_cci_stub_endpoint():
    client = TestClient(app)
    response = client.get("/api/backtest/cci")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "cci"
    assert data["bars_processed"] == 0
    assert data["metrics"] is None


def test_run_backtest_not_found_endpoint():
    client = TestClient(app)
    response = client.get("/api/backtest/unknown_strategy")
    assert response.status_code == 404


def test_run_backtest_rsi_sma_endpoint():
    client = TestClient(app)
    # Use small period to speed up the test
    url = "/api/backtest/rsi_sma?symbol=AAPL&period=5d&interval=1d"
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "rsi_sma"
    assert "equity_curve" in data
    assert "metrics" in data
    assert "cumulative_returns" in data
    assert "trades" in data


def test_get_telemetry_history_endpoint():
    client = TestClient(app)
    # Write a dummy telemetry line to verify parsing
    from alpha_kd.telemetry import TelemetryBuffer
    from pathlib import Path

    tel_path = Path("telemetry.jsonl")
    buffer = TelemetryBuffer(tel_path)
    buffer.record({"test_key": "test_val"})

    response = client.get("/api/telemetry/history?n=5")
    assert response.status_code == 200
    data = response.json()
    assert "records" in data
    assert "total_records" in data
    assert data["total_records"] > 0
    assert data["records"][-1]["test_key"] == "test_val"


# ---------------------------------------------------------------------------
# Milestone 4A — Parameterized Research Runs
# ---------------------------------------------------------------------------


def test_backtest_default_parameters_used_field():
    """Default run must include parameters_used == DEFAULT_PARAMS."""
    client = TestClient(app)
    response = client.get("/api/backtest/rsi_sma?symbol=AAPL&period=5d&interval=1d")
    assert response.status_code == 200
    data = response.json()
    assert "parameters_used" in data
    p = data["parameters_used"]
    assert p["fast_sma"] == 10
    assert p["slow_sma"] == 20
    assert p["rsi"] == 14
    assert pytest.approx(p["tp"]) == 0.01
    assert pytest.approx(p["sl"]) == -0.01
    assert pytest.approx(p["cost"]) == 0.0001
    assert p["leverage"] == 1


def test_backtest_single_param_override():
    """Single override merges with defaults; others stay at default."""
    client = TestClient(app)
    response = client.get(
        "/api/backtest/rsi_sma?symbol=AAPL&period=5d&interval=1d&fast_sma=5"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parameters_used"]["fast_sma"] == 5
    assert data["parameters_used"]["slow_sma"] == 20


def test_backtest_full_param_override():
    """All 7 params overridden; parameters_used reflects all supplied values."""
    client = TestClient(app)
    url = (
        "/api/backtest/rsi_sma"
        "?symbol=AAPL&period=5d&interval=1d"
        "&fast_sma=5&slow_sma=15&rsi=10"
        "&tp=0.02&sl=-0.02&cost=0.0002&leverage=2"
    )
    response = client.get(url)
    assert response.status_code == 200
    data = response.json()
    p = data["parameters_used"]
    assert p["fast_sma"] == 5
    assert p["slow_sma"] == 15
    assert p["rsi"] == 10
    assert pytest.approx(p["tp"]) == 0.02
    assert pytest.approx(p["sl"]) == -0.02
    assert pytest.approx(p["cost"]) == 0.0002
    assert p["leverage"] == 2


def test_backtest_validation_slow_sma_not_greater_than_fast_sma():
    """slow_sma <= fast_sma must return 422."""
    client = TestClient(app)
    response = client.get(
        "/api/backtest/rsi_sma?fast_sma=20&slow_sma=10"
    )
    assert response.status_code == 422


def test_backtest_validation_slow_sma_equal_fast_sma():
    """slow_sma == fast_sma must return 422."""
    client = TestClient(app)
    response = client.get(
        "/api/backtest/rsi_sma?fast_sma=10&slow_sma=10"
    )
    assert response.status_code == 422


def test_backtest_validation_sl_must_be_negative():
    """sl >= 0 must return 422."""
    client = TestClient(app)
    response = client.get("/api/backtest/rsi_sma?sl=0.01")
    assert response.status_code == 422


def test_backtest_validation_sl_zero_rejected():
    """sl == 0 must return 422."""
    client = TestClient(app)
    response = client.get("/api/backtest/rsi_sma?sl=0.0")
    assert response.status_code == 422


def test_backtest_validation_tp_must_be_positive():
    """tp <= 0 must return 422."""
    client = TestClient(app)
    response = client.get("/api/backtest/rsi_sma?tp=-0.01")
    assert response.status_code == 422


def test_backtest_validation_leverage_must_be_positive():
    """leverage <= 0 must return 422."""
    client = TestClient(app)
    response = client.get("/api/backtest/rsi_sma?leverage=0")
    assert response.status_code == 422


def test_backtest_cci_unaffected_by_params():
    """CCI stub returns 200 regardless of param overrides."""
    client = TestClient(app)
    response = client.get("/api/backtest/cci?fast_sma=5&slow_sma=15")
    assert response.status_code == 200
    data = response.json()
    assert data["strategy_id"] == "cci"
    assert data["metrics"] is None


def test_backtest_rsi_sma_regime_accepts_params():
    """rsi_sma_regime also accepts param overrides."""
    client = TestClient(app)
    response = client.get(
        "/api/backtest/rsi_sma_regime?symbol=AAPL&period=5d&interval=1d&fast_sma=5&slow_sma=15"
    )
    assert response.status_code == 200
    data = response.json()
    assert data["parameters_used"]["fast_sma"] == 5
    assert data["parameters_used"]["slow_sma"] == 15
