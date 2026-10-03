"""Adım 4 — Referans görseller (Bölüm 6): ara, indir, puanla, sahnelere ata (refs/manifest.json)."""
from __future__ import annotations

from collections import defaultdict
from pathlib import PurePosixPath

from core import prompts, rules
from core.pipeline.context import JobContext, StepError

MIN_SCORE = 6.0


def _needs(script: dict) -> dict[str, list[str]]:
    needs: dict[str, list[str]] = defaultdict(list)
    for shot in script["shots"]:
        for tag in shot["refs_needed"]:
            needs[tag].append(shot["id"])
    return dict(needs)


def run(ctx: JobContext) -> None:
    script = ctx.read_json("script.json")
    shot_ids = [s["id"] for s in script["shots"]]
    manifest_path = ctx.job_dir / "refs" / "manifest.json"
    if manifest_path.exists() and not rules.check_refs_cover_shots(ctx.read_json("refs", "manifest.json"), shot_ids):
        ctx.log.write("refs", "skip", reason="manifest.json zaten tüm sahneleri kapsıyor")
        return

    cfg = ctx.config["image_search"]
    _, max_per_need = cfg["refs_per_shot"]
    search = ctx.providers.image_search
    refs: list[dict] = []
    for tag, shots in _needs(script).items():
        need = tag.replace("_", " ")
        candidates = search.search(f"{ctx.idea['device']} {need}", cfg["candidates_per_category"])
        files = []
        for i, cand in enumerate(candidates):
            suffix = PurePosixPath(cand.url).suffix.lower() or ".jpg"
            dest = ctx.path("refs", tag, f"{i:02d}{suffix}")
            if not dest.exists():
                search.download(cand, dest)
            files.append(dest)
        if not files:
            continue
        prompt = prompts.fill(ctx.prompt("ref_scoring"), device=ctx.idea["device"], need=need)
        scored = ctx.llm_json("ref_score", prompt, "ref_scores", images=files, context={"need": tag})
        score_of = {s["index"]: s["score"] for s in scored["scores"]}
        ranked = sorted(range(len(files)), key=lambda i: -score_of.get(i, 0))
        for i in [i for i in ranked if score_of.get(i, 0) >= MIN_SCORE][:max_per_need]:
            cand = candidates[i]
            refs.append({
                "ref_id": f"R{len(refs) + 1:03d}", "category": tag,
                "local_path": files[i].relative_to(ctx.job_dir).as_posix(),
                "source_url": cand.url, "source": cand.source, "license": cand.license,
                "author": cand.author, "internal_only": cand.internal_only, "score": score_of[i],
                "description": f"{need} reference: {cand.title}", "assigned_shots": shots,
            })

    manifest = {"refs": refs}
    missing = rules.check_refs_cover_shots(manifest, shot_ids)
    if missing:
        raise StepError("Referans görsel eksik: " + "; ".join(missing))
    ctx.write_json(manifest, "refs", "manifest.json")
    ctx.log.write("refs", "done", refs=len(refs), needs=len(_needs(script)))
