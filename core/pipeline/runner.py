"""Bir job'u bulunduğu durumdan itibaren üretim hattında ilerletir.

Her adım idempotent olduğu için bilgisayar kapanırsa run_job() tekrar çağrılır ve kaldığı
yerden devam eder. Hata ya da bütçe tavanında job needs_attention'a düşer ve bildirim gider.
"""
from __future__ import annotations

import time
import traceback
from collections.abc import Callable

from core import states
from core.costs import BudgetExceeded
from core.pipeline import assemble, keyframes, qc, refs, research, script, sfx, shots, voice
from core.pipeline.context import JobContext, StepError

# (adım adı, fonksiyon, adım bitince geçilecek durum)
STEPS: list[tuple[str, Callable[[JobContext], object], str | None]] = [
    ("research", research.run, states.RESEARCHING),
    ("script", script.run, states.SCRIPTED),
    ("refs", refs.run, states.REFS_READY),
    ("keyframes", keyframes.run, states.KEYFRAMES_READY),
    ("voice", voice.run, states.VOICED),
    ("shots", shots.run, states.SHOTS_READY),
    ("sfx", sfx.run, None),
    ("assemble", assemble.run, states.ASSEMBLED),
    ("qc", qc.run, None),
]

# Durum → hangi adımdan başlanacağı. "researching" araştırmayı yeniden dener (dosya varsa atlar).
START_AT = {
    states.QUEUED: "research", states.RESEARCHING: "research", states.SCRIPTED: "refs",
    states.REFS_READY: "keyframes", states.KEYFRAMES_READY: "voice", states.VOICED: "shots",
    states.SHOTS_READY: "sfx", states.ASSEMBLED: "qc",
}
_INDEX = {name: i for i, (name, _, _) in enumerate(STEPS)}

Notifier = Callable[[str, str, str], None]  # (başlık, mesaj, job_id)


def _status(ctx: JobContext) -> str:
    return ctx.conn.execute("SELECT status FROM jobs WHERE id = ?", (ctx.job_id,)).fetchone()["status"]


def _attention(ctx: JobContext, notify: Notifier, step: str, reason: str) -> str:
    ctx.log.write(step, "needs_attention", reason=reason)
    states.mark_attention(ctx.conn, ctx.job_id, f"[{step}] {reason}")
    notify("Müdahale gerekiyor", f"{ctx.job_id} ({ctx.idea['title']}) — {step}: {reason}", ctx.job_id)
    return states.NEEDS_ATTENTION


def run_job(ctx: JobContext, notify: Notifier) -> str:
    status = _status(ctx)
    if status not in START_AT:
        return status
    for name, fn, done in STEPS[_INDEX[START_AT[status]]:]:
        ctx.step = name
        started, cost_before = time.monotonic(), ctx.ledger.job_total(ctx.job_id)
        ctx.log.write(name, "start")
        try:
            result = fn(ctx)
        except (BudgetExceeded, StepError) as e:
            return _attention(ctx, notify, name, str(e))
        except Exception as e:
            ctx.log.write(name, "error", traceback=traceback.format_exc())
            return _attention(ctx, notify, name, f"Beklenmeyen hata: {type(e).__name__}: {e}")
        ctx.log.write(name, "end", duration_s=round(time.monotonic() - started, 2),
                      cost_usd=round(ctx.ledger.job_total(ctx.job_id) - cost_before, 4))
        if done and _status(ctx) != done:
            states.transition(ctx.conn, ctx.job_id, done)
        if name == "qc":
            if result:
                states.transition(ctx.conn, ctx.job_id, states.AUTO_QC_PASSED)
                states.transition(ctx.conn, ctx.job_id, states.AWAITING_REVIEW)
                notify("Yeni video incelemede", f"{ctx.job_id} — {ctx.idea['title']}", ctx.job_id)
            else:
                states.transition(ctx.conn, ctx.job_id, states.REJECTED_AUTO)
                notify("Otomatik kontrol reddetti", f"{ctx.job_id} — ayrıntılar qc_report.json'da", ctx.job_id)
    return _status(ctx)
