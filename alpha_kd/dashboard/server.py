import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from alpha_kd.telemetry.logger import TelemetryBuffer
from alpha_kd.dashboard.control_state import get_control, update_control


class DashboardHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.static_dir = Path(__file__).parent / "static"
        super().__init__(*args, directory=str(self.static_dir), **kwargs)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            buf = TelemetryBuffer(Path("telemetry.jsonl"))
            logs = buf.tail(50)

            control = get_control()
            response_data = {
                "logs": logs,
                "loading": control["loading"],
                "mode": control["mode"],
                "action": control["action"],
            }
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/control":
            content_length = int(self.headers.get("Content-Length", 0))
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode("utf-8"))
                update_control(data)
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                res = {"status": "ok", "control": get_control()}
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                res = {"status": "error", "message": str(e)}
                self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self.send_response(404)
            self.end_headers()


def start_dashboard(port: int = 8080):
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Dashboard serving at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
