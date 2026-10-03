"""Adım 7 — Video sahneleri (shots/S01.mp4 …).

Hibrit modda (Bölüm 13) yalnızca hareketin şart olduğu sahneler Seedance ile üretilir;
video başı AI süresi max_ai_video_seconds_per_video ile sınırlıdır. Diğer sahneler anahtar
kareler üzerinde FFmpeg kamera hareketiyle yapılır (ücretsiz).
"""
from __future__ import annotations

import zlib
from concurrent.futures import ThreadPoolExecutor

from core import db, prompts, rules
from core.pipeline import visual
from core.pipeline.context import JobContext, StepError

_PRIORITY = {"high": 0, "medium": 1, "low": 2}
QC_FPS = 2


def plan_modes(shots: list[dict], timing: dict, video_cfg: dict) -> dict[str, str]:
    """Her sahne için "ai" ya da "kenburns" seçer."""
    if video_cfg["mode"] == "full_ai":
        return {s["id"]: "ai" for s in shots}
    gen = {t["id"]: t["gen_s"] for t in timing["shots"]}
    budget = video_cfg["max_ai_video_seconds_per_video"]
    modes = {s["id"]: "kenburns" for s in shots}
    used = 0
    for s in sorted(shots, key=lambda s: (_PRIORITY[s["motion_importance"]], s["id"])):
        if s["motion_importance"] == "low":
            continue
        if used + gen[s["id"]] <= budget:
            modes[s["id"]] = "ai"
            used += gen[s["id"]]
    return modes


def _seed(job_id: str, shot_id: str, attempt: int) -> int:
    return (zlib.crc32(f"{job_id}:{shot_id}".encode()) + attempt) % 2**31


def _ai_shot(ctx: JobContext, shot: dict, timing: dict, n_shots: int) -> dict:
    vcfg = ctx.config["video"]
    first = ctx.job_dir / "keyframes" / f"{shot['start_keyframe']}.png"
    last = ctx.job_dir / "keyframes" / f"{shot['end_keyframe']}.png"
    out = ctx.path("shots", f"{shot['id']}.mp4")
    gen_s, resolution = timing["gen_s"], vcfg["resolution"]
    fix_notes: list[str] = []
    for attempt in range(vcfg["max_shot_retries"] + 1):
        prompt = prompts.shot_prompt(forbidden=ctx.forbidden, shot=shot, n_shots=n_shots, duration_s=gen_s,
                                     start_desc=shot["start_frame_desc"], end_desc=shot["end_frame_desc"],
                                     fix_notes=fix_notes)
        errs = rules.check_shot_prompt(prompt, ctx.forbidden)
        if errs:
            raise StepError(f"{shot['id']} promptu kurallara uymuyor: " + "; ".join(errs))
        seed = _seed(ctx.job_id, shot["id"], attempt)
        generate_audio = False  # Kural 2: video modelinden ses alınmaz
        rules.assert_silent_video_request(generate_audio)
        usd = ctx.ledger.video_cost(gen_s, resolution)
        with ctx.paid("fal_seedance", usd, gen_s, f"{shot['id']} {resolution}"):
            ctx.providers.video.image_to_video(
                first_frame=first, last_frame=last, prompt=prompt, duration_s=gen_s, resolution=resolution,
                aspect_ratio=ctx.config["format"]["aspect_ratio"], seed=seed, out_path=out,
                generate_audio=generate_audio)
        ctx.path("shots", "prompts", f"{shot['id']}.txt").write_text(prompt, encoding="utf-8")
        db.add_asset(ctx.conn, ctx.job_id, "shot", out.relative_to(ctx.job_dir).as_posix(), seed=seed, cost=usd)
        frames = ctx.providers.renderer.sample_frames(out, QC_FPS, ctx.job_dir / "shots" / "frames" / f"{shot['id']}_{attempt}")
        qc = visual.check(ctx, target=shot["id"], candidates=frames, refs=[first, last],
                          description=f"{shot['start_frame_desc']} -> {shot['end_frame_desc']}")
        ctx.log.write("shots", "qc", shot=shot["id"], attempt=attempt, passed=qc["pass"], seed=seed)
        if qc["pass"]:
            return {"mode": "ai", "pass": True, "attempt": attempt, "seed": seed, "scores": qc["scores"]}
        fix_notes = [qc["fix_instructions"]] if qc["fix_instructions"] else []
    raise StepError(f"{shot['id']}: {vcfg['max_shot_retries'] + 1} denemede sahne kontrolünden geçemedi "
                    f"({'; '.join(qc['fatal'] + qc['problems'])})")


def run(ctx: JobContext) -> None:
    script, timing = ctx.read_json("script.json"), ctx.read_json("audio", "timing.json")
    shots = script["shots"]
    by_id = {t["id"]: t for t in timing["shots"]}
    plan_path = ctx.job_dir / "shots" / "plan.json"
    modes = ctx.read_json("shots", "plan.json") if plan_path.exists() else plan_modes(shots, timing, ctx.config["video"])
    ctx.write_json(modes, "shots", "plan.json")
    qc_path = ctx.job_dir / "shots" / "qc.json"
    qc_log = ctx.read_json("shots", "qc.json") if qc_path.exists() else {}

    todo = [s for s in shots if not ((ctx.job_dir / "shots" / f"{s['id']}.mp4").exists()
                                     and qc_log.get(s["id"], {}).get("pass"))]
    for s in [s for s in todo if modes[s["id"]] == "kenburns"]:
        out = ctx.path("shots", f"{s['id']}.mp4")
        ctx.providers.renderer.kenburns(
            start_frame=ctx.job_dir / "keyframes" / f"{s['start_keyframe']}.png",
            end_frame=ctx.job_dir / "keyframes" / f"{s['end_keyframe']}.png",
            duration_s=by_id[s["id"]]["target_s"], out_path=out)
        db.add_asset(ctx.conn, ctx.job_id, "shot", out.relative_to(ctx.job_dir).as_posix())
        qc_log[s["id"]] = {"mode": "kenburns", "pass": True}

    ai = [s for s in todo if modes[s["id"]] == "ai"]
    try:
        with ThreadPoolExecutor(max_workers=ctx.config["video"]["max_concurrent_video_jobs"]) as pool:
            futures = {s["id"]: pool.submit(_ai_shot, ctx, s, by_id[s["id"]], len(shots)) for s in ai}
            errors = []
            for shot_id, fut in futures.items():
                try:
                    qc_log[shot_id] = fut.result()
                except Exception as e:  # diğer sahneler bitsin, sonra ilk hatayı yükselt
                    errors.append(e)
            if errors:
                raise errors[0]
    finally:
        ctx.write_json(qc_log, "shots", "qc.json")
    ai_s = sum(by_id[s["id"]]["gen_s"] for s in shots if modes[s["id"]] == "ai")
    ctx.log.write("shots", "done", ai_shots=sum(m == "ai" for m in modes.values()), ai_seconds=ai_s)
