"""Adım 8 — Ses efektleri (audio/sfx_*.wav). Müzik asla yok (Kural 2).

Sık kullanılan efektler assets/sfx_cache/ altında bir kez üretilir ve tekrar kullanılır.
"""
from __future__ import annotations

import hashlib
import shutil

from core import rules
from core.pipeline.context import JobContext

MAX_SFX_S = 5.0
MIN_SFX_S = 0.5


def run(ctx: JobContext) -> None:
    if (ctx.job_dir / "audio" / "sfx.json").exists():
        ctx.log.write("sfx", "skip", reason="sfx.json zaten var")
        return
    script, timing = ctx.read_json("script.json"), ctx.read_json("audio", "timing.json")
    by_id = {t["id"]: t for t in timing["shots"]}
    cache = ctx.assets_dir / "sfx_cache"
    cache.mkdir(parents=True, exist_ok=True)
    suffix = ctx.channel["sfx_suffix"]

    events, generated, reused = [], 0, 0
    for shot in script["shots"]:
        start, length = by_id[shot["id"]]["start_s"], by_id[shot["id"]]["target_s"]
        for n, ev in enumerate(shot["sfx"]):
            prompt = rules.sfx_prompt(ev["prompt"], suffix)
            t = min(max(ev["t"], 0.0), max(length - MIN_SFX_S, 0.0))
            duration = round(min(max(length - t, MIN_SFX_S), MAX_SFX_S), 1)
            cached = cache / f"{hashlib.sha1(f'{prompt}|{duration}'.encode()).hexdigest()[:16]}.wav"
            if cached.exists():
                reused += 1
            else:
                with ctx.paid("elevenlabs_sfx", ctx.ledger.sfx_cost(), 1, prompt[:60]):
                    ctx.providers.sfx.generate(prompt=prompt, duration_s=duration, out_path=cached)
                generated += 1
            dest = ctx.path("audio", f"sfx_{shot['id']}_{n}.wav")
            shutil.copyfile(cached, dest)
            events.append({"shot": shot["id"], "t": round(start + t, 3), "duration_s": duration,
                           "path": dest.relative_to(ctx.job_dir).as_posix(), "prompt": prompt})
    ctx.write_json({"events": events}, "audio", "sfx.json")
    ctx.log.write("sfx", "done", events=len(events), generated=generated, reused=reused)
