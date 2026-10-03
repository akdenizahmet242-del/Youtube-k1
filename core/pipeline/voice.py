"""Adım 6 — Seslendirme (audio/voice.mp3 + audio/words.json) ve sahne süreleri (audio/timing.json).

Sahne süresi = o sahnenin anlatım süresi + pay (config: video.narration_padding_s).
Üretim süresi bunun Seedance'in kabul ettiği tam saniyeye yukarı yuvarlanmış halidir (en az 4 sn);
montajda hedef süreye kırpılır.
"""
from __future__ import annotations

import math

from core.pipeline.context import JobContext, StepError


def run(ctx: JobContext) -> None:
    voice = ctx.path("audio", "voice.mp3")
    if voice.exists() and (ctx.job_dir / "audio" / "timing.json").exists():
        ctx.log.write("voice", "skip", reason="seslendirme ve zamanlama zaten var")
        return
    script = ctx.read_json("script.json")
    shots = script["shots"]
    fmt, vcfg = ctx.config["format"], ctx.config["video"]
    text = " ".join(s["narration"].strip() for s in shots)

    with ctx.paid("elevenlabs_tts", ctx.ledger.tts_cost(len(text)), len(text)):
        words = ctx.providers.tts.synthesize(text=text, voice_id=ctx.channel["narrator"]["voice_id"], out_path=voice)
    ctx.write_json([{"word": w.word, "start": w.start, "end": w.end} for w in words], "audio", "words.json")

    counts = [len(s["narration"].split()) for s in shots]
    if len(words) != sum(counts):
        raise StepError(f"Zaman damgalı kelime sayısı ({len(words)}) anlatımla ({sum(counts)}) uyuşmuyor")

    timeline, out_words, t, idx = [], [], 0.0, 0
    for shot, n in zip(shots, counts):
        seg = words[idx:idx + n]
        idx += n
        narration_s = seg[-1].end - seg[0].start
        target = round(max(narration_s + vcfg["narration_padding_s"], fmt["min_shot_s"]), 3)
        gen = min(max(math.ceil(target), vcfg["min_generation_s"]), vcfg["max_generation_s"])
        timeline.append({"id": shot["id"], "start_s": round(t, 3), "target_s": target, "gen_s": gen,
                         "audio_from_s": seg[0].start, "audio_to_s": seg[-1].end})
        out_words += [{"word": w.word, "start": round(t + w.start - seg[0].start, 3),
                       "end": round(t + w.end - seg[0].start, 3), "shot": shot["id"]} for w in seg]
        t += target

    total = round(t, 3)
    if not fmt["min_duration_s"] <= total <= fmt["max_duration_s"]:
        raise StepError(f"Seslendirmeye göre toplam süre {total} sn; {fmt['min_duration_s']}–"
                        f"{fmt['max_duration_s']} sn olmalı. Anlatım kısaltılmalı/uzatılmalı.")
    ctx.write_json({"total_s": total, "shots": timeline, "words": out_words}, "audio", "timing.json")
    ctx.log.write("voice", "done", words=len(words), total_s=total)
