"""Job durum makinesi (Bölüm 5).

queued → researching → scripted → refs_ready → keyframes_ready → voiced → shots_ready
→ assembled → auto_qc_passed → awaiting_review → (approved | needs_revision | rejected)
→ scheduled → published

Ek durumlar:
- needs_attention: bir adım tekrar denemelere rağmen başarısız oldu ya da bütçe tavanına
  takıldı. Önceki durum prev_status'ta saklanır; resume() ile oradan devam edilir.
- rejected_auto: otomatik kalite kontrolü videoyu reddetti; ilgili sahneler yeniden üretilir.
"""
from __future__ import annotations

import sqlite3

from core.db import utcnow

QUEUED = "queued"
RESEARCHING = "researching"
SCRIPTED = "scripted"
REFS_READY = "refs_ready"
KEYFRAMES_READY = "keyframes_ready"
VOICED = "voiced"
SHOTS_READY = "shots_ready"
ASSEMBLED = "assembled"
AUTO_QC_PASSED = "auto_qc_passed"
AWAITING_REVIEW = "awaiting_review"
APPROVED = "approved"
NEEDS_REVISION = "needs_revision"
REJECTED = "rejected"
SCHEDULED = "scheduled"
PUBLISHED = "published"
NEEDS_ATTENTION = "needs_attention"
REJECTED_AUTO = "rejected_auto"

# Üretim hattı sırası: her biri bir önceki adımın tamamlandığını gösterir.
PIPELINE = [
    QUEUED, RESEARCHING, SCRIPTED, REFS_READY, KEYFRAMES_READY, VOICED,
    SHOTS_READY, ASSEMBLED, AUTO_QC_PASSED, AWAITING_REVIEW,
]

# Düzeltme ve otomatik ret, üretim hattında geri sarılabileceği durumlar.
REWIND_TARGETS = {SCRIPTED, REFS_READY, KEYFRAMES_READY, VOICED, SHOTS_READY}

TRANSITIONS: dict[str, set[str]] = {
    QUEUED: {RESEARCHING},
    RESEARCHING: {SCRIPTED},
    SCRIPTED: {REFS_READY},
    REFS_READY: {KEYFRAMES_READY},
    KEYFRAMES_READY: {VOICED},
    VOICED: {SHOTS_READY},
    SHOTS_READY: {ASSEMBLED},
    ASSEMBLED: {AUTO_QC_PASSED, REJECTED_AUTO},
    AUTO_QC_PASSED: {AWAITING_REVIEW},
    AWAITING_REVIEW: {APPROVED, NEEDS_REVISION, REJECTED},
    NEEDS_REVISION: REWIND_TARGETS,
    REJECTED_AUTO: REWIND_TARGETS,
    APPROVED: {SCHEDULED},
    SCHEDULED: {PUBLISHED, APPROVED},  # slottan çıkarılırsa onaylıya döner
    PUBLISHED: set(),
    REJECTED: set(),
    NEEDS_ATTENTION: set(),  # yalnızca resume() ile çıkılır
}

TERMINAL = {PUBLISHED, REJECTED}
# Bu durumlardayken üretim hattı çalışıyor demektir (tampon hesabında "üretimde").
IN_PRODUCTION = set(PIPELINE[:PIPELINE.index(AUTO_QC_PASSED) + 1]) | {NEEDS_REVISION, REJECTED_AUTO, NEEDS_ATTENTION}


class InvalidTransition(Exception):
    pass


def can_transition(current: str, new: str) -> bool:
    if new == NEEDS_ATTENTION:
        return current not in TERMINAL and current != NEEDS_ATTENTION
    return new in TRANSITIONS.get(current, set())


def transition(conn: sqlite3.Connection, job_id: str, new: str) -> None:
    row = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row is None:
        raise KeyError(f"job bulunamadı: {job_id}")
    current = row["status"]
    if new == NEEDS_ATTENTION:
        raise InvalidTransition("needs_attention için mark_attention() kullan")
    if not can_transition(current, new):
        raise InvalidTransition(f"{job_id}: {current} → {new} geçişi geçersiz")
    conn.execute("UPDATE jobs SET status = ?, updated_at = ? WHERE id = ?", (new, utcnow(), job_id))


def mark_attention(conn: sqlite3.Connection, job_id: str, reason: str) -> None:
    current = conn.execute("SELECT status FROM jobs WHERE id = ?", (job_id,)).fetchone()["status"]
    if not can_transition(current, NEEDS_ATTENTION):
        raise InvalidTransition(f"{job_id}: {current} → needs_attention geçişi geçersiz")
    conn.execute(
        "UPDATE jobs SET status = ?, prev_status = ?, attention_reason = ?, updated_at = ? WHERE id = ?",
        (NEEDS_ATTENTION, current, reason, utcnow(), job_id),
    )


def resume(conn: sqlite3.Connection, job_id: str) -> str:
    row = conn.execute("SELECT status, prev_status FROM jobs WHERE id = ?", (job_id,)).fetchone()
    if row["status"] != NEEDS_ATTENTION:
        raise InvalidTransition(f"{job_id} needs_attention durumunda değil")
    conn.execute(
        "UPDATE jobs SET status = ?, prev_status = NULL, attention_reason = NULL, updated_at = ? WHERE id = ?",
        (row["prev_status"], utcnow(), job_id),
    )
    return row["prev_status"]
