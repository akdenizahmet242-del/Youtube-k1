"""Adım 9 — Montaj (final/<job_id>.mp4) ve kapak karesi (final/thumbnail.png)."""
from __future__ import annotations

from core import db
from core.pipeline.context import JobContext

THUMBNAIL_AT_S = 1.5  # kanca sahnesinden bir kare


def run(ctx: JobContext) -> None:
    final = ctx.path("final", f"{ctx.job_id}.mp4")
    thumb = ctx.path("final", "thumbnail.png")
    if final.exists() and thumb.exists():
        ctx.log.write("assemble", "skip", reason="final video zaten var")
        return
    script, timing = ctx.read_json("script.json"), ctx.read_json("audio", "timing.json")
    sfx = ctx.read_json("audio", "sfx.json")["events"]
    shots = [ctx.job_dir / "shots" / f"{s['id']}.mp4" for s in script["shots"]]
    renderer = ctx.providers.renderer
    renderer.assemble(job_dir=ctx.job_dir, script=script, timing=timing, shots=shots, sfx=sfx, out_path=final)
    renderer.thumbnail(video=final, at_s=THUMBNAIL_AT_S, out_path=thumb)
    for kind, path in (("final", final), ("thumbnail", thumb)):
        db.add_asset(ctx.conn, ctx.job_id, kind, path.relative_to(ctx.job_dir).as_posix())
    ctx.log.write("assemble", "done", duration_s=timing["total_s"])
