"""Adım 3 — Senaryo ve sahne listesi (script.json), Bölüm 7.2 promptu ile."""
from __future__ import annotations

from core import prompts, rules
from core.pipeline.context import JobContext, StepError


def run(ctx: JobContext) -> None:
    if ctx.valid_json("script", "script.json"):
        ctx.log.write("script", "skip", reason="script.json zaten geçerli")
        return
    idea, facts = ctx.idea, ctx.read_json("facts.json")
    fact_ids = [f["id"] for f in facts["facts"]]
    prompt = prompts.fill(
        ctx.prompt("script_planner"),
        title=idea["title"], device=idea["device"], real_world_context=idea["real_world_context"],
        mechanism=idea["mechanism"], chain_to_result=idea["chain_to_result"],
        facts_json=facts["facts"], components_json=facts["components"],
    )
    if idea.get("hook_question"):
        prompt += f"\n\nUse this hook question if it is supported by the facts: {idea['hook_question']}"
    prompt = prompts.with_learnings(prompt, ctx.lessons)

    script = ctx.llm_json("script", prompt, "script", context={"idea": idea, "fact_ids": fact_ids})
    script["job_id"] = ctx.job_id
    errs, warns = rules.validate_script(script, ctx.config["format"], set(fact_ids))
    for w in warns:
        ctx.log.write("script", "warning", message=w)
    if errs:
        raise StepError("Senaryo kurallara uymuyor: " + "; ".join(errs))
    ctx.write_json(script, "script.json")
    ctx.log.write("script", "done", shots=len(script["shots"]), duration_s=script["total_duration_s"])
