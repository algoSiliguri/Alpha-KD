import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

from alpha_kd.telemetry.logger import TelemetryBuffer


class DashboardHandler(SimpleHTTPRequestHandler):

    def __init__(self, *args, **kwargs):
        self.static_dir = Path(__file__).parent / "static"
        super().__init__(*args, directory=str(self.static_dir), **kwargs)

    def do_GET(self):
        if self.path == "/api/telemetry":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            buf = TelemetryBuffer(Path("telemetry.jsonl"))
            logs = buf.tail(50)
            self.wfile.write(json.dumps(logs).encode("utf-8"))
        else:
            super().do_GET()


def start_dashboard(port: int = 8080):
    server = HTTPServer(("127.0.0.1", port), DashboardHandler)
    print(f"Dashboard serving at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
