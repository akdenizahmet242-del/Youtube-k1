"""Aşama 2 kabul testi: maliyet tavanı job'u durdurur."""
from datetime import datetime, timezone

import pytest

from core import states
from core.app import NewJobBlocked
from core.costs import BudgetExceeded


def test_per_video_cap_stops_job(make_app, config):
    config["budget"]["max_cost_per_video"] = 3.0
    app = make_app(cfg=config)
    job_id = app.create_job("diesel-engine")
    assert app.run(job_id) == states.NEEDS_ATTENTION
    job = app.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    assert "Bütçe tavanı (video)" in job["attention_reason"]
    assert app.ledger.job_total(job_id) <= 3.0


def test_monthly_cap_blocks_new_jobs(make_app):
    app = make_app()
    app.ledger.record(None, "test", 1, 950.0)
    with pytest.raises(NewJobBlocked):
        app.create_job("cpu")


def test_daily_cap_blocks_new_jobs(make_app):
    app = make_app()
    app.ledger.record(None, "test", 1, 46.0)
    with pytest.raises(NewJobBlocked):
        app.create_job("cpu")


def test_guard_counts_month_in_local_timezone(make_app):
    # 1 Kasım 00:30 İstanbul = 31 Ekim 21:30 UTC → Ekim harcaması Kasım'a sayılmamalı
    now = datetime(2026, 10, 31, 21, 30, tzinfo=timezone.utc)
    app = make_app(clock=lambda: now)
    app.conn.execute("INSERT INTO costs (ts, job_id, service, units, usd) VALUES (?, NULL, 'x', 1, 999)",
                     ("2026-10-31T20:00:00+00:00",))
    app.ledger.guard(None, 40.0)  # yeni ay: geçer
    app.conn.execute("INSERT INTO costs (ts, job_id, service, units, usd) VALUES (?, NULL, 'x', 1, 30)",
                     ("2026-10-31T21:15:00+00:00",))
    with pytest.raises(BudgetExceeded):
        app.ledger.guard(None, 25.0)  # aynı gün 30 + 25 > 50


def test_parallel_reservations_respect_cap(make_app, config):
    config["budget"]["max_cost_per_video"] = 2.0
    app = make_app(cfg=config)
    job_id = app.create_job("cpu")
    t1 = app.ledger.reserve(job_id, 1.5)
    with pytest.raises(BudgetExceeded):
        app.ledger.reserve(job_id, 1.0)  # ilk çağrı henüz kaydedilmedi ama ayrıldı
    app.ledger.release(t1)
    app.ledger.reserve(job_id, 1.0)
