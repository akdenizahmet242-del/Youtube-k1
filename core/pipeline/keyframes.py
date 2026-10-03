"""Adım 5 — Anahtar kareler (keyframes/K00.png … K{N}.png).

N sahne için N+1 kare sırayla üretilir. Sahne i, K(i-1) ile başlar ve K(i) ile biter.
Her kare 7.6 kontrolünden geçmeli; geçemezse en fazla 3 deneme, sonra needs_attention.
"""
from __future__ import annotations

from pathlib import Path

from core import db, prompts, rules
from core.pipeline import visual
from core.pipeline.context import JobContext, StepError

MAX_OBJECT_REFS = 6
MAX_STYLE_REFS = 3


def _style_library(ctx: JobContext) -> list[Path]:
    folder = ctx.channel_dir / "style_refs"
    return sorted(p for p in folder.glob("*") if p.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"})


def run(ctx: JobContext) -> None:
    script = ctx.read_json("script.json")
    manifest = ctx.read_json("refs", "manifest.json")
    shots = script["shots"]
    qc_log = ctx.read_json("keyframes", "qc.json") if (ctx.job_dir / "keyframes" / "qc.json").exists() else {}
    kcfg = ctx.config["keyframes"]
    library = _style_library(ctx)

    for i in range(len(shots) + 1):
        kf = f"K{i:02d}"
        out = ctx.path("keyframes", f"{kf}.png")
        if out.exists() and qc_log.get(kf, {}).get("pass"):
            continue
        shot, which = (shots[0], "start") if i == 0 else (shots[i - 1], "end")
        desc = shot["start_frame_desc"] if which == "start" else shot["end_frame_desc"]
        using = {s["id"] for s in shots if kf in (s["start_keyframe"], s["end_keyframe"])}
        refs = sorted((r for r in manifest["refs"] if using & set(r["assigned_shots"])),
                      key=lambda r: -r["score"])[:MAX_OBJECT_REFS]
        if not refs:
            raise StepError(f"{kf}: referans görsel yok (Kural 6)")
        ref_paths = [ctx.job_dir / r["local_path"] for r in refs]
        prev = ctx.job_dir / "keyframes" / f"K{i - 1:02d}.png" if i else None
        style = ([prev] if prev else []) + library
        style = style[:MAX_STYLE_REFS]

        fix_notes: list[str] = []
        for attempt in range(1, kcfg["max_retries"] + 1):
            prompt = prompts.keyframe_prompt(
                channel=ctx.channel, forbidden=ctx.forbidden, kf_id=kf, which=which, shot=shot,
                frame_desc=desc, refs=refs, prev_kf=f"K{i - 1:02d}" if i else None,
                lessons=ctx.lessons, fix_notes=fix_notes)
            errs = rules.check_keyframe_prompt(prompt, ctx.forbidden)
            if errs:
                raise StepError(f"{kf} promptu kurallara uymuyor: " + "; ".join(errs))
            usd = ctx.ledger.image_cost()
            with ctx.paid("gemini_image", usd, 1, kf):
                ctx.providers.image.generate(prompt=prompt, ref_images=ref_paths, style_images=style,
                                             out_path=out, aspect_ratio=ctx.config["format"]["aspect_ratio"],
                                             image_size=kcfg["image_size"])
            ctx.path("keyframes", "prompts", f"{kf}.txt").write_text(prompt, encoding="utf-8")
            db.add_asset(ctx.conn, ctx.job_id, "keyframe", out.relative_to(ctx.job_dir).as_posix(), cost=usd)
            qc = visual.check(ctx, target=kf, candidates=[out], refs=ref_paths, description=desc)
            qc_log[kf] = {"pass": qc["pass"], "attempt": attempt, "scores": qc["scores"],
                          "problems": qc["problems"], "fatal": qc["fatal"]}
            ctx.write_json(qc_log, "keyframes", "qc.json")
            ctx.log.write("keyframes", "qc", keyframe=kf, attempt=attempt, passed=qc["pass"])
            if qc["pass"]:
                break
            fix_notes = [qc["fix_instructions"]] if qc["fix_instructions"] else []
        else:
            raise StepError(f"{kf}: {kcfg['max_retries']} denemede kalite kontrolünden geçemedi "
                            f"({'; '.join(qc['fatal'] + qc['problems'])})")
    ctx.log.write("keyframes", "done", keyframes=len(shots) + 1)
