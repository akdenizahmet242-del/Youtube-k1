"""Adım 10 — Final videonun otomatik kalite kontrolü (Bölüm 9). Rapor: qc_report.json"""
from __future__ import annotations

from core.pipeline import visual
from core.pipeline.context import JobContext

FRAMES_PER_CALL = 20
LOUDNESS_TOLERANCE = 1.0


def run(ctx: JobContext) -> bool:
    fmt, audio = ctx.config["format"], ctx.channel["audio"]
    final = ctx.job_dir / "final" / f"{ctx.job_id}.mp4"
    renderer = ctx.providers.renderer
    info = renderer.probe(final)
    checks: list[dict] = []

    def check(name: str, ok: bool, detail: str) -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail})

    check("Süre", fmt["min_duration_s"] <= info.duration_s <= fmt["max_duration_s"],
          f"{info.duration_s:.1f} sn (izin: {fmt['min_duration_s']}–{fmt['max_duration_s']})")
    check("Çözünürlük", (info.width, info.height) == (fmt["width"], fmt["height"]), f"{info.width}×{info.height}")
    check("Kare hızı", abs(info.fps - fmt["fps"]) < 0.01, f"{info.fps:g} fps")
    lufs_ok = info.loudness_lufs is not None and abs(info.loudness_lufs - audio["loudness_lufs"]) <= LOUDNESS_TOLERANCE
    check("Ses seviyesi", lufs_ok, f"{info.loudness_lufs} LUFS (hedef {audio['loudness_lufs']})")
    music = renderer.music_suspected(final)
    check("Müzik yok", not music, "şüpheli tonal içerik bulundu" if music else "müzik/ton algılanmadı")

    timing, script = ctx.read_json("audio", "timing.json"), ctx.read_json("script.json")
    narration_words = sum(len(s["narration"].split()) for s in script["shots"])
    check("Altyazı senkronu", len(timing["words"]) == narration_words,
          f"{len(timing['words'])}/{narration_words} kelime zaman damgalı")

    # Kadın/insan, yazı/logo: tüm video boyunca saniyede 1 kare (Bölüm 9).
    frames = renderer.sample_frames(final, 1, ctx.job_dir / "qc_frames")
    worst = None
    for i in range(0, len(frames), FRAMES_PER_CALL):
        batch = frames[i:i + FRAMES_PER_CALL]
        qc = visual.check(ctx, target="final", candidates=batch, refs=[],
                          description=f"Final video frames {i}–{i + len(batch) - 1} (1 fps)")
        if worst is None or not qc["pass"]:
            worst = qc
        if not qc["pass"]:
            break
    check("Görsel kontrol (insan/kadın, yazı/logo, gerçekçilik)", worst["pass"],
          "sorun yok" if worst["pass"] else "; ".join(worst["fatal"] + worst["problems"]))

    passed = all(c["ok"] for c in checks)
    score = round(sum(worst["scores"].values()) / len(worst["scores"]), 2)
    ctx.write_json({"pass": passed, "score": score, "checks": checks, "visual": worst}, "qc_report.json")
    ctx.conn.execute("UPDATE jobs SET qc_score = ? WHERE id = ?", (score, ctx.job_id))
    ctx.log.write("qc", "done", passed=passed, score=score)
    return passed
