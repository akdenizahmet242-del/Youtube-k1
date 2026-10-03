"""Bildirimler (Bölüm 10.3). Şimdilik konsola ve data/notifications.jsonl dosyasına yazar;
masaüstü ve Telegram bildirimleri Aşama 8'de eklenecek. Mesajlar Türkçe.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.db import utcnow


def notify(log_path: Path, title: str, message: str, *, job_id: str | None = None) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps({"ts": utcnow(), "title": title, "message": message, "job_id": job_id},
                           ensure_ascii=False) + "\n")
    print(f"🔔 {title}: {message}")
