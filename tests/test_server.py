import json
import threading
import time
import urllib.request
import urllib.error
from http.server import HTTPServer
import pytest

from alpha_kd.dashboard.server import DashboardHandler
from alpha_kd.dashboard.control_state import get_control


@pytest.fixture
def run_test_server():
    server = HTTPServer(("127.0.0.1", 0), DashboardHandler)
    port = server.server_address[1]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    time.sleep(0.1)  # Allow server to start
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    server.server_close()
    thread.join()


def test_get_telemetry(run_test_server):
    url = f"{run_test_server}/api/telemetry"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert "logs" in data
        assert "loading" in data
        assert "mode" in data
        assert "action" in data
        assert isinstance(data["logs"], list)


def test_post_control(run_test_server):
    url = f"{run_test_server}/api/control"
    payload = json.dumps({
        "mode": "Forward Test (Simulated Live)",
        "action": "start",
        "loading": True
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST"
    )
    with urllib.request.urlopen(req) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data["status"] == "ok"
        assert data["control"]["mode"] == "Forward Test (Simulated Live)"
        assert data["control"]["action"] == "start"
        assert data["control"]["loading"] is True

    # Verify global control state updated
    ctrl = get_control()
    assert ctrl["mode"] == "Forward Test (Simulated Live)"
    assert ctrl["action"] == "start"
    assert ctrl["loading"] is True
