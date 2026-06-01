import json
import tempfile
from pathlib import Path

from alpha_kd.telemetry import TelemetryBuffer


def _make_buf(tmp_dir, max_records=10_000):
    return TelemetryBuffer(Path(tmp_dir) / "telemetry.jsonl", max_records=max_records)


def test_record_appends_json_line():
    with tempfile.TemporaryDirectory() as tmp:
        buf = _make_buf(tmp)
        buf.record({"side": "flat", "signal": 0})
        buf.record({"side": "buy", "signal": 1})
        lines = (Path(tmp) / "telemetry.jsonl").read_text().splitlines()
        assert len(lines) == 2
        assert json.loads(lines[0]) == {"side": "flat", "signal": 0}
        assert json.loads(lines[1]) == {"side": "buy", "signal": 1}


def test_tail_returns_last_n():
    with tempfile.TemporaryDirectory() as tmp:
        buf = _make_buf(tmp)
        for i in range(5):
            buf.record({"i": i})
        result = buf.tail(3)
        assert result == [{"i": 2}, {"i": 3}, {"i": 4}]


def test_tail_empty_buffer():
    with tempfile.TemporaryDirectory() as tmp:
        buf = _make_buf(tmp)
        assert buf.tail(5) == []


def test_flush_truncates_to_max_records():
    with tempfile.TemporaryDirectory() as tmp:
        buf = _make_buf(tmp, max_records=10_000)
        for i in range(12_000):
            buf.record({"i": i})
        lines = (Path(tmp) / "telemetry.jsonl").read_text().splitlines()
        assert len(lines) == 10_000
        assert json.loads(lines[-1])["i"] == 11_999
        assert json.loads(lines[0])["i"] == 2_000
