"""Adım 2 — Araştırma: doğrulanmış gerçekler ve gerçek bileşen listesi (facts.json)."""
from __future__ import annotations

from core import prompts, rules
from core.pipeline.context import JobContext, StepError


def run(ctx: JobContext) -> None:
    if ctx.valid_json("facts", "facts.json"):
        ctx.log.write("research", "skip", reason="facts.json zaten geçerli")
        return
    idea = ctx.idea
    prompt = prompts.fill(ctx.prompt("research"), title=idea["title"], device=idea["device"],
                          mechanism=idea["mechanism"], chain_to_result=idea["chain_to_result"])
    facts = ctx.llm_json("research", prompt, "facts", web_search=True, context={"idea": idea})
    errs = rules.validate_facts(facts)
    if errs:
        raise StepError("Araştırma kurallara uymuyor: " + "; ".join(errs))
    ctx.write_json(facts, "facts.json")
    ctx.log.write("research", "done", facts=len(facts["facts"]), components=len(facts["components"]))
