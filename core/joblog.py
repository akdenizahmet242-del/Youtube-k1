"""Her adımın girdisi, çıktısı, maliyeti, süresi ve hataları: jobs/<job_id>/log.jsonl"""
from __future__ import annotations

import json
import threading
from pathlib import Path

from core.db import utcnow


class JobLog:
    def __init__(self, job_dir: Path):
        self.path = job_dir / "log.jsonl"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def write(self, step: str, event: str, **data) -> None:
        record = {"ts": utcnow(), "step": step, "event": event, **data}
        with self._lock, open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

    def read(self) -> list[dict]:
        if not self.path.exists():
            return []
        with open(self.path, encoding="utf-8") as f:
            return [json.loads(line) for line in f if line.strip()]
