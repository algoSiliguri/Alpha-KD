"""Append-only JSONL telemetry with ring-buffer truncation. Stdlib only."""
import json
from pathlib import Path
from typing import List


class TelemetryBuffer:
    def __init__(self, path: Path, max_records: int = 10_000):
        self.path = Path(path)
        self.max_records = max_records
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._count = self._count_lines()

    def _count_lines(self) -> int:
        if not self.path.exists():
            return 0
        try:
            with self.path.open() as f:
                return sum(1 for _ in f)
        except Exception:
            return 0

    def record(self, state: dict) -> None:
        """Append a state snapshot as one JSON line."""
        try:
            with self.path.open("a") as f:
                f.write(json.dumps(state) + "\n")
            self._count += 1
            if self._count > self.max_records:
                self.flush()
        except Exception:
            pass

    def tail(self, n: int = 1) -> List[dict]:
        """Return the last n records."""
        if not self.path.exists():
            return []
        try:
            with self.path.open() as f:
                lines = f.readlines()
            return [json.loads(line) for line in lines[-n:] if line.strip()]
        except Exception:
            return []

    def flush(self) -> None:
        """Truncate file to max_records if exceeded."""
        if not self.path.exists():
            return
        try:
            with self.path.open() as f:
                lines = f.readlines()
            if len(lines) <= self.max_records:
                return
            kept = lines[-self.max_records:]
            tmp = self.path.with_suffix(".tmp")
            with tmp.open("w") as f:
                f.writelines(kept)
            tmp.rename(self.path)
            self._count = self.max_records
        except Exception:
            pass
