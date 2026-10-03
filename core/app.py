"""Sistemin giriş noktası: ayarlar, veritabanı, bütçe ve sağlayıcıları bir araya getirir."""
from __future__ import annotations

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml

from core import db, notify, settings, states
from core.costs import Ledger
from core.joblog import JobLog
from core.pipeline import runner
from core.pipeline.context import JobContext
from core.providers import build_providers
from core.providers.base import Providers


class NewJobBlocked(Exception):
    """Bütçe tavanı nedeniyle yeni job başlatılmadı."""


@dataclass
class App:
    config: dict
    data_root: Path
    conn: sqlite3.Connection
    ledger: Ledger
    providers: Providers
    channel: dict
    channel_dir: Path

    @classmethod
    def open(cls, *, config: dict | None = None, data_root: Path = settings.ROOT,
             providers: Providers | None = None, provider_mode: str | None = None,
             clock: Callable[[], datetime] | None = None) -> App:
        settings.load_env()
        config = config or settings.load_config()
        conn = db.connect(cls._resolve(data_root, config["paths"]["db_path"]))
        channel_id = config["channel"]
        return cls(
            config=config, data_root=data_root, conn=conn, ledger=Ledger(conn, config, clock),
            providers=providers or build_providers(config, provider_mode),
            channel=settings.load_channel(channel_id), channel_dir=settings.channel_dir(channel_id),
        )

    @staticmethod
    def _resolve(root: Path, path: str) -> Path:
        p = Path(path)
        return p if p.is_absolute() else root / p

    def path(self, key: str) -> Path:
        return self._resolve(self.data_root, self.config["paths"][key])

    # --- fikirler ve job'lar ---------------------------------------------
    def sync_ideas(self) -> int:
        with open(self.channel_dir / "ideas.yaml", encoding="utf-8") as f:
            ideas = yaml.safe_load(f)["ideas"]
        return db.upsert_ideas(self.conn, self.channel["id"], ideas)

    def create_job(self, idea_id: str) -> str:
        ok, reason = self.ledger.can_start_new_job()
        if not ok:
            self.notify("Bütçe uyarısı", reason)
            raise NewJobBlocked(reason)
        db.get_idea(self.conn, idea_id)  # yoksa KeyError
        prefix = self.channel["job_prefix"]
        row = self.conn.execute("SELECT id FROM jobs WHERE id LIKE ? ORDER BY id DESC LIMIT 1",
                                (f"{prefix}-%",)).fetchone()
        number = int(row["id"].rsplit("-", 1)[1]) + 1 if row else 1
        job_id, now = f"{prefix}-{number:04d}", db.utcnow()
        self.conn.execute(
            "INSERT INTO jobs (id, channel, idea_id, status, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (job_id, self.channel["id"], idea_id, states.QUEUED, now, now))
        self.conn.execute("UPDATE ideas SET status = 'in_use', last_used_at = ? WHERE id = ?", (now, idea_id))
        return job_id

    def context(self, job_id: str) -> JobContext:
        job = db.get_job(self.conn, job_id)
        job_dir = self.path("jobs_dir") / job_id
        return JobContext(
            job_id=job_id, job_dir=job_dir, idea=db.get_idea(self.conn, job["idea_id"]), config=self.config,
            channel=self.channel, channel_dir=self.channel_dir, assets_dir=self.path("assets_dir"),
            conn=self.conn, ledger=self.ledger, log=JobLog(job_dir), providers=self.providers,
        )

    def run(self, job_id: str) -> str:
        return runner.run_job(self.context(job_id), lambda title, msg, jid: self.notify(title, msg, jid))

    def notify(self, title: str, message: str, job_id: str | None = None) -> None:
        notify.notify(self.path("db_path").parent / "notifications.jsonl", title, message, job_id=job_id)
