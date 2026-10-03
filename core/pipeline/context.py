"""Bir job'un adımlar arasında paylaşılan bağlamı."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

from core import prompts, schemas
from core.costs import Ledger
from core.joblog import JobLog
from core.providers.base import LLMResult, Providers


class StepError(Exception):
    """Adım, yeniden denemelere rağmen tamamlanamadı; job needs_attention'a düşer."""


@dataclass
class JobContext:
    job_id: str
    job_dir: Path
    idea: dict
    config: dict
    channel: dict
    channel_dir: Path
    assets_dir: Path
    conn: sqlite3.Connection
    ledger: Ledger
    log: JobLog
    providers: Providers
    step: str = ""

    # --- dosyalar --------------------------------------------------------
    def path(self, *parts: str) -> Path:
        p = self.job_dir.joinpath(*parts)
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def read_json(self, *parts: str) -> dict:
        return json.loads(self.job_dir.joinpath(*parts).read_text(encoding="utf-8"))

    def write_json(self, data: object, *parts: str) -> Path:
        p = self.path(*parts)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(p)  # yarım yazılmış dosya kalmasın (idempotent adımlar için)
        return p

    def valid_json(self, schema: str, *parts: str) -> bool:
        p = self.job_dir.joinpath(*parts)
        if not p.exists():
            return False
        try:
            return not schemas.errors(schema, json.loads(p.read_text(encoding="utf-8")))
        except json.JSONDecodeError:
            return False

    # --- promptlar -------------------------------------------------------
    def prompt(self, name: str) -> str:
        return prompts.load(self.channel_dir, self.channel, name)

    @property
    def forbidden(self) -> str:
        return self.prompt("forbidden")

    @property
    def lessons(self) -> list[str]:
        return prompts.learnings(self.channel_dir)

    # --- ücretli çağrılar ------------------------------------------------
    @contextmanager
    def paid(self, service: str, usd: float, units: float, note: str = ""):
        """Çağrıdan önce bütçe tavanını denetler; çağrı başarılı olursa harcamayı kaydeder."""
        token = self.ledger.reserve(self.job_id, usd)
        try:
            yield
        except BaseException:
            self.ledger.release(token)
            raise
        self.ledger.commit(token, service, units, note)
        self.log.write(self.step, "cost", service=service, usd=usd, units=units, note=note)

    def llm_json(self, task: str, prompt: str, schema: str, *, images: list[Path] = (),
                 web_search: bool = False, context: dict | None = None) -> dict:
        token = self.ledger.reserve(self.job_id, self.config["pricing"]["llm_call_estimate"])
        try:
            result: LLMResult = self.providers.llm.complete_json(
                task=task, prompt=prompt, schema=schemas.load(schema), images=list(images),
                web_search=web_search, context=context)
        finally:
            self.ledger.release(token)
        usd = self.ledger.llm_cost(result.input_tokens, result.output_tokens)
        self.ledger.record(self.job_id, "anthropic", result.input_tokens + result.output_tokens, usd, task)
        self.log.write(self.step, "cost", service="anthropic", usd=usd, task=task,
                       input_tokens=result.input_tokens, output_tokens=result.output_tokens)
        errs = schemas.errors(schema, result.data)
        if errs:
            raise StepError(f"{task}: LLM çıktısı şemaya uymuyor: {errs[:3]}")
        return result.data
