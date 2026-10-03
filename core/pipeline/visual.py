"""Görsel kalite kontrolü (Bölüm 7.6): anahtar kare, sahne ve final videoda ortak."""
from __future__ import annotations

import json
from pathlib import Path

from core.pipeline.context import JobContext


def passes(qc: dict, pass_score: float) -> bool:
    """LLM'in "pass" alanına tek başına güvenilmez: ölümcül sorun yok ve her puan eşiğin üstünde olmalı."""
    return bool(qc["pass"]) and not qc["fatal"] and min(qc["scores"].values()) >= pass_score


def check(ctx: JobContext, *, target: str, candidates: list[Path], refs: list[Path], description: str) -> dict:
    components = ctx.read_json("facts.json")["components"]
    prompt = (
        f"{ctx.prompt('visual_qc')}\n\n"
        f"CHECK TARGET: {target}\n"
        f"SHOT DESCRIPTION: {description}\n"
        f"COMPONENT LIST: {json.dumps(components, ensure_ascii=False)}\n"
        f"ATTACHED IMAGES: the first {len(candidates)} image(s) are the candidate"
        f"{' frames' if len(candidates) > 1 else ''}; the remaining {len(refs)} are references, in order."
    )
    qc = ctx.llm_json("visual_qc", prompt, "visual_qc", images=[*candidates, *refs], context={"target": target})
    qc["pass"] = passes(qc, ctx.config["keyframes"]["pass_score"])
    return qc
