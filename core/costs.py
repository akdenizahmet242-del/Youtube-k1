"""Maliyet kaydı ve bütçe koruması (Bölüm 13).

- Her ücretli çağrıdan ÖNCE guard() çağrılır: video, gün ya da ay tavanı aşılacaksa
  BudgetExceeded fırlatılır ve job needs_attention durumuna düşer.
- Her çağrıdan SONRA record() ile gerçek maliyet costs tablosuna ve job'a yazılır.
- Gün/ay harcaması tavanın stop_new_jobs_ratio oranına gelince yeni job başlamaz.
"""
from __future__ import annotations

import itertools
import sqlite3
import threading
from collections.abc import Callable
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


class BudgetExceeded(Exception):
    def __init__(self, scope: str, spent: float, estimate: float, limit: float):
        self.scope, self.spent, self.estimate, self.limit = scope, spent, estimate, limit
        super().__init__(
            f"Bütçe tavanı ({scope}): harcanan {spent:.2f} $ + bu adım {estimate:.2f} $ > tavan {limit:.2f} $"
        )


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="seconds")


class Ledger:
    def __init__(self, conn: sqlite3.Connection, config: dict,
                 clock: Callable[[], datetime] | None = None):
        self.conn = conn
        self.budget = config["budget"]
        self.pricing = config["pricing"]
        self.tz = ZoneInfo(config["schedule"]["local_timezone"])
        self.clock = clock or (lambda: datetime.now(timezone.utc))
        # Paralel çağrılar (ör. aynı anda 3 video) tavanı birlikte aşamasın diye
        # onaylanmış ama henüz kaydedilmemiş harcamalar burada tutulur.
        self._lock = threading.RLock()
        self._pending: dict[int, tuple[str | None, float]] = {}
        self._ids = itertools.count(1)

    # --- toplamlar -------------------------------------------------------
    def _sum_since(self, start: datetime) -> float:
        row = self.conn.execute("SELECT COALESCE(SUM(usd), 0) AS s FROM costs WHERE ts >= ?", (_iso(start),)).fetchone()
        return float(row["s"])

    def job_total(self, job_id: str) -> float:
        row = self.conn.execute("SELECT COALESCE(SUM(usd), 0) AS s FROM costs WHERE job_id = ?", (job_id,)).fetchone()
        return float(row["s"])

    def day_total(self) -> float:
        now = self.clock().astimezone(self.tz)
        return self._sum_since(now.replace(hour=0, minute=0, second=0, microsecond=0))

    def month_total(self) -> float:
        now = self.clock().astimezone(self.tz)
        return self._sum_since(now.replace(day=1, hour=0, minute=0, second=0, microsecond=0))

    # --- koruma ----------------------------------------------------------
    def guard(self, job_id: str | None, estimate_usd: float) -> None:
        with self._lock:
            self._check(job_id, estimate_usd)

    def _check(self, job_id: str | None, estimate_usd: float) -> None:
        pending_all = sum(usd for _, usd in self._pending.values())
        pending_job = sum(usd for j, usd in self._pending.values() if j == job_id)
        checks = [
            ("ay", self.month_total() + pending_all, self.budget["max_cost_per_month"]),
            ("gün", self.day_total() + pending_all, self.budget["max_cost_per_day"]),
        ]
        if job_id is not None:
            checks.append(("video", self.job_total(job_id) + pending_job, self.budget["max_cost_per_video"]))
        for scope, spent, limit in checks:
            if spent + estimate_usd > limit + 1e-9:
                raise BudgetExceeded(scope, spent, estimate_usd, limit)

    def reserve(self, job_id: str | None, usd: float) -> int:
        """Tavanı denetler ve tutarı ayırır. Çağrı bitince commit() ya da release() çağrılır."""
        with self._lock:
            self._check(job_id, usd)
            token = next(self._ids)
            self._pending[token] = (job_id, usd)
            return token

    def commit(self, token: int, service: str, units: float, note: str | None = None) -> None:
        with self._lock:
            job_id, usd = self._pending.pop(token)
            self.record(job_id, service, units, usd, note)

    def release(self, token: int) -> None:
        with self._lock:
            self._pending.pop(token, None)

    def can_start_new_job(self) -> tuple[bool, str]:
        ratio = self.budget["stop_new_jobs_ratio"]
        est = self.budget["estimated_cost_per_video"]
        month, day = self.month_total(), self.day_total()
        if month >= ratio * self.budget["max_cost_per_month"] or month + est > self.budget["max_cost_per_month"]:
            return False, f"Aylık harcama {month:.2f} $; tavan {self.budget['max_cost_per_month']:.0f} $. Yeni job başlatılmadı."
        if day >= ratio * self.budget["max_cost_per_day"] or day + est > self.budget["max_cost_per_day"]:
            return False, f"Günlük harcama {day:.2f} $; tavan {self.budget['max_cost_per_day']:.0f} $. Yeni job başlatılmadı."
        return True, ""

    # --- kayıt -----------------------------------------------------------
    def record(self, job_id: str | None, service: str, units: float, usd: float, note: str | None = None) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT INTO costs (ts, job_id, service, units, usd, note) VALUES (?, ?, ?, ?, ?, ?)",
                (_iso(self.clock()), job_id, service, units, usd, note),
            )
            if job_id is not None:
                self.conn.execute("UPDATE jobs SET cost_usd = cost_usd + ? WHERE id = ?", (usd, job_id))

    # --- fiyat tahminleri -------------------------------------------------
    def video_cost(self, seconds: float, resolution: str) -> float:
        return round(seconds * self.pricing["seedance_per_s"][resolution], 4)

    def image_cost(self, count: int = 1) -> float:
        return round(count * self.pricing["keyframe_image"], 4)

    def tts_cost(self, chars: int) -> float:
        return round(chars / 1000 * self.pricing["tts_per_1k_chars"], 4)

    def sfx_cost(self, calls: int = 1) -> float:
        return round(calls * self.pricing["sfx_per_call"], 4)

    def llm_cost(self, input_tokens: int, output_tokens: int) -> float:
        return round(input_tokens / 1e6 * self.pricing["llm_input_per_mtok"]
                     + output_tokens / 1e6 * self.pricing["llm_output_per_mtok"], 4)
