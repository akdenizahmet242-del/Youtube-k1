"""Aşama 2 kabul testi: sahte sağlayıcılarla bir job tüm durumlardan geçer."""
import json

from core import states
from core.providers import mock


def test_job_goes_through_all_states(make_app):
    app = make_app()
    job_id = app.create_job("diesel-engine")
    assert app.run(job_id) == states.AWAITING_REVIEW

    ctx = app.context(job_id)
    for f in ["facts.json", "script.json", "refs/manifest.json", "keyframes/K00.png", "keyframes/K11.png",
              "audio/voice.mp3", "audio/words.json", "audio/timing.json", "shots/S01.mp4", "shots/S11.mp4",
              "audio/sfx.json", f"final/{job_id}.mp4", "final/thumbnail.png", "qc_report.json", "log.jsonl"]:
        assert (ctx.job_dir / f).exists(), f
    steps = [r["step"] for r in ctx.log.read() if r["event"] == "end"]
    assert steps == ["research", "script", "refs", "keyframes", "voice", "shots", "sfx", "assemble", "qc"]
    assert json.loads((ctx.job_dir / "qc_report.json").read_text())["pass"] is True
    # Maliyet hem costs tablosunda hem job kaydında
    assert app.ledger.job_total(job_id) > 0
    row = app.conn.execute("SELECT cost_usd FROM jobs WHERE id = ?", (job_id,)).fetchone()
    assert abs(row["cost_usd"] - app.ledger.job_total(job_id)) < 1e-6


def test_rerun_is_idempotent(make_app):
    app = make_app()
    job_id = app.create_job("cpu")
    app.run(job_id)
    spent = app.ledger.job_total(job_id)
    # Bilgisayar kapanmış gibi: durumu geri sar, tekrar çalıştır → hiçbir şey yeniden üretilmez
    app.conn.execute("UPDATE jobs SET status = ? WHERE id = ?", (states.RESEARCHING, job_id))
    assert app.run(job_id) == states.AWAITING_REVIEW
    assert app.ledger.job_total(job_id) - spent < 0.2  # yalnızca final kalite kontrolü tekrarlanır


def test_keyframe_retry_after_failed_qc(make_app, config):
    providers = mock.build(config, fail_qc={"K03": 1})
    app = make_app(providers=providers)
    job_id = app.create_job("refrigerator")
    assert app.run(job_id) == states.AWAITING_REVIEW
    qc = app.context(job_id).read_json("keyframes", "qc.json")
    assert qc["K03"]["attempt"] == 2 and qc["K03"]["pass"]


def test_keyframe_gives_up_after_three_attempts(make_app, config):
    providers = mock.build(config, fail_qc={"K02": 5})
    app = make_app(providers=providers)
    job_id = app.create_job("ssd")
    assert app.run(job_id) == states.NEEDS_ATTENTION
    job = app.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
    assert job["prev_status"] == states.REFS_READY
    assert "K02" in job["attention_reason"]
    assert len(providers.image.prompts) == 2 + 3  # K00, K01 + K02 için 3 deneme
