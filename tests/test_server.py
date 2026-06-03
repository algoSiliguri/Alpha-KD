import json
import threading
import time
import urllib.request

from alpha_kd.dashboard.control_state import get_control
from alpha_kd.dashboard.server import start_dashboard


def test_dashboard_server_endpoints():
    port = 18080
    t = threading.Thread(target=start_dashboard, args=(port,), daemon=True)
    t.start()
    time.sleep(0.5)

    url_control = f"http://127.0.0.1:{port}/api/control"
    req_data = json.dumps({
        "mode": "Paper Trading (Real-Time Live)",
        "action": "start",
    }).encode("utf-8")
    req = urllib.request.Request(
        url_control,
        data=req_data,
        headers={"Content-Type": "application/json"},
    )

    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert res["status"] == "success"

    ctrl = get_control()
    assert ctrl["mode"] == "Paper Trading (Real-Time Live)"
    assert ctrl["action"] == "start"

    url_telemetry = f"http://127.0.0.1:{port}/api/telemetry"
    with urllib.request.urlopen(url_telemetry) as resp:
        res = json.loads(resp.read().decode("utf-8"))
        assert "logs" in res
        assert "loading" in res
        assert "mode" in res
        assert "action" in res
        assert res["mode"] == "Paper Trading (Real-Time Live)"
        assert res["action"] == "start"
