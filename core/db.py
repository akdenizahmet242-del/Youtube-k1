"""SQLite veritabanı (Bölüm 14): jobs, assets, reviews, costs, ideas."""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS ideas (
    id            TEXT PRIMARY KEY,
    channel       TEXT NOT NULL,
    title         TEXT NOT NULL,
    category      TEXT NOT NULL,
    data          TEXT NOT NULL,              -- fikrin tamamı (JSON)
    status        TEXT NOT NULL DEFAULT 'available',
    last_used_at  TEXT
);

CREATE TABLE IF NOT EXISTS jobs (
    id                TEXT PRIMARY KEY,
    channel           TEXT NOT NULL,
    idea_id           TEXT REFERENCES ideas(id),
    status            TEXT NOT NULL,
    prev_status       TEXT,                   -- needs_attention'dan dönülecek durum
    attention_reason  TEXT,
    version           INTEGER NOT NULL DEFAULT 1,
    created_at        TEXT NOT NULL,
    updated_at        TEXT NOT NULL,
    cost_usd          REAL NOT NULL DEFAULT 0,
    qc_score          REAL,
    slot_date         TEXT,
    slot_index        INTEGER
);
CREATE INDEX IF NOT EXISTS jobs_status ON jobs(status);

CREATE TABLE IF NOT EXISTS assets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id       TEXT NOT NULL REFERENCES jobs(id),
    kind         TEXT NOT NULL,               -- keyframe | shot | voice | sfx | final | ref ...
    path         TEXT NOT NULL,
    version      INTEGER NOT NULL DEFAULT 1,
    prompt_hash  TEXT,
    seed         INTEGER,
    cost         REAL NOT NULL DEFAULT 0,
    created_at   TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS assets_job ON assets(job_id, kind);

CREATE TABLE IF NOT EXISTS reviews (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    job_id      TEXT NOT NULL REFERENCES jobs(id),
    version     INTEGER NOT NULL,
    decision    TEXT NOT NULL,                -- approved | needs_revision | rejected | regenerate
    notes       TEXT,
    tags        TEXT,                         -- JSON liste
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS costs (
    id       INTEGER PRIMARY KEY AUTOINCREMENT,
    ts       TEXT NOT NULL,                   -- UTC ISO-8601
    job_id   TEXT,
    service  TEXT NOT NULL,
    units    REAL NOT NULL,
    usd      REAL NOT NULL,
    note     TEXT
);
CREATE INDEX IF NOT EXISTS costs_ts ON costs(ts);
"""


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def connect(path: Path | str) -> sqlite3.Connection:
    if str(path) != ":memory:":
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, check_same_thread=False, isolation_level=None)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    conn.executescript(SCHEMA)
    return conn


def upsert_ideas(conn: sqlite3.Connection, channel: str, ideas: list[dict]) -> int:
    """ideas.yaml'ı veritabanına aktarır. Var olan fikirlerin durumu korunur."""
    for idea in ideas:
        conn.execute(
            """
            INSERT INTO ideas (id, channel, title, category, data, status)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET title = excluded.title,
                category = excluded.category, data = excluded.data
            """,
            (idea["id"], channel, idea["title"], idea["category"], json.dumps(idea, ensure_ascii=False),
             idea.get("status", "available")),
        )
    return len(ideas)


def get_idea(conn: sqlite3.Connection, idea_id: str) -> dict:
    row = conn.execute("SELECT data FROM ideas WHERE id = ?", (idea_id,)).fetchone()
    if row is None:
        raise KeyError(f"fikir bulunamadı: {idea_id}")
    return json.loads(row["data"])


def get_job(conn: sqlite3.Connection, job_id: str) -> sqlite3.Row:
    row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"job bulunamadı: {job_id}")
    return row


def add_asset(conn: sqlite3.Connection, job_id: str, kind: str, path: Path | str, *, version: int = 1,
              prompt_hash: str | None = None, seed: int | None = None, cost: float = 0.0) -> None:
    conn.execute(
        "INSERT INTO assets (job_id, kind, path, version, prompt_hash, seed, cost, created_at)"
        " VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (job_id, kind, str(path), version, prompt_hash, seed, cost, utcnow()),
    )
