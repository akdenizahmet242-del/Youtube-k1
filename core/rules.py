"""Bölüm 2'deki değişmez kuralların kod içindeki denetimleri.

Her pipeline adımı ilgili denetimi çağırır. Bir denetim hata listesi döndürürse adım
durur; kurallar kolaylıklara karşı her zaman kazanır.

1 Kadın yok, varsayılan olarak insan yok  → yasak listesi her görsel/video promptunda;
                                            senaryoda kadın ifadesi yasak; kalite kontrolü.
2 Müzik yok                               → video isteğinde generate_audio=False;
                                            SFX promptlarına "no music" eki.
3 Shorts formatı                          → validate_script() süre/sahne sınırları.
4 Aşırı ayrıntılı promptlar               → check_keyframe_prompt(), check_shot_prompt().
6 Referans görseller                      → check_refs_cover_shots().
7 Otomatik yükleme yok                    → sistemde YouTube yükleme kodu yoktur.
8 Tam zincir                              → validate_script() 6 vuruşu ister.
"""
from __future__ import annotations

import re

KEYFRAME_HEADERS = [
    "[1 PURPOSE]", "[2 REFERENCES]", "[3 SUBJECT]", "[4 COMPOSITION]", "[5 LIGHTING]",
    "[6 MATERIALS & COLOR CODE]", "[7 CONTINUITY]", "[8 PHOTOREALISM]", "[9 FORBIDDEN]",
]
SHOT_HEADERS = ["[SHOT]", "[START]", "[END]", "[CAMERA]", "[MOTION", "[KEEP CONSTANT]", "[FORBIDDEN]"]

# Kare tarifinin "aşırı ayrıntılı" sayılması için en az kelime sayısı.
MIN_SUBJECT_WORDS = 40

_FEMALE = re.compile(r"\b(woman|women|girl|girls|female|females|lady|ladies|mother|daughter|actress|she|her)\b", re.I)
_NEGATION = re.compile(r"\b(no|not|never|without|nor)\b[\w\s,]{0,20}$", re.I)


def female_mentions(text: str) -> list[str]:
    """Olumsuzlanmamış kadın ifadelerini döndürür ("no woman" gibi yasaklar sayılmaz)."""
    found = []
    for m in _FEMALE.finditer(text):
        if not _NEGATION.search(text[max(0, m.start() - 30):m.start()]):
            found.append(m.group(0))
    return found


def _section(prompt: str, header: str, headers: list[str]) -> str:
    start = prompt.find(header)
    if start < 0:
        return ""
    start += len(header)
    ends = [prompt.find(h, start) for h in headers if prompt.find(h, start) >= 0]
    return prompt[start:min(ends) if ends else len(prompt)].strip()


def check_keyframe_prompt(prompt: str, forbidden: str) -> list[str]:
    errs = [f"başlık eksik: {h}" for h in KEYFRAME_HEADERS if h not in prompt]
    if forbidden.strip() not in prompt:
        errs.append("yasak listesi (7.1) eksiksiz eklenmemiş")
    subject = _section(prompt, "[3 SUBJECT]", KEYFRAME_HEADERS)
    if len(subject.split()) < MIN_SUBJECT_WORDS:
        errs.append(f"[3 SUBJECT] çok kısa ({len(subject.split())} kelime < {MIN_SUBJECT_WORDS})")
    errs += [f"promptta kadın ifadesi: '{w}'" for w in female_mentions(prompt.replace(forbidden.strip(), ""))]
    return errs


def check_shot_prompt(prompt: str, forbidden: str) -> list[str]:
    errs = [f"başlık eksik: {h}" for h in SHOT_HEADERS if h not in prompt]
    if forbidden.strip() not in prompt:
        errs.append("yasak listesi (7.1) eksiksiz eklenmemiş")
    if not re.search(r"\d+(\.\d+)?\s*-\s*\d+(\.\d+)?s:", prompt):
        errs.append("[MOTION] zamanlı adım içermiyor (ör. '0.0-1.5s: ...')")
    errs += [f"promptta kadın ifadesi: '{w}'" for w in female_mentions(prompt.replace(forbidden.strip(), ""))]
    return errs


def assert_silent_video_request(generate_audio: bool) -> None:
    if generate_audio:
        raise ValueError("Kural 2: video modelinde ses üretimi kapalı olmalı (generate_audio=False)")


def sfx_prompt(prompt: str, suffix: str) -> str:
    prompt = prompt.strip().rstrip(".")
    return prompt if prompt.endswith(suffix) else f"{prompt}, {suffix}"


def _sentences(text: str) -> list[str]:
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def validate_facts(facts: dict) -> list[str]:
    errs = []
    for f in facts["facts"]:
        if f["value"] is not None and len({s["url"] for s in f["sources"]}) < 2:
            errs.append(f"{f['id']}: sayısal iddia en az iki bağımsız kaynakla doğrulanmalı")
    return errs


def validate_script(script: dict, fmt: dict, fact_ids: set[str]) -> tuple[list[str], list[str]]:
    """Senaryoyu kurallara göre denetler. (hatalar, uyarılar) döndürür."""
    errs, warns = [], []
    shots = script["shots"]
    if not fmt["min_shots"] <= len(shots) <= fmt["max_shots"]:
        errs.append(f"sahne sayısı {len(shots)}; {fmt['min_shots']}–{fmt['max_shots']} olmalı")

    beats = [s["beat"] for s in shots]
    if beats != sorted(beats):
        errs.append("vuruşlar sırayla ilerlemeli (1→6)")
    missing = sorted(set(range(1, 7)) - set(beats))
    if missing:
        errs.append(f"eksik vuruş(lar): {missing} — 6 vuruşlu iskelet ve tam zincir zorunlu")

    for i, s in enumerate(shots):
        if s["id"] != f"S{i + 1:02d}":
            errs.append(f"{s['id']}: sahne kimliği S{i + 1:02d} olmalı")
        if s["start_keyframe"] != f"K{i:02d}" or s["end_keyframe"] != f"K{i + 1:02d}":
            errs.append(f"{s['id']}: K{i:02d} ile başlayıp K{i + 1:02d} ile bitmeli")
        if not fmt["min_shot_s"] <= s["duration_s"] <= fmt["max_shot_s"]:
            errs.append(f"{s['id']}: süre {s['duration_s']} sn; {fmt['min_shot_s']}–{fmt['max_shot_s']} olmalı")
        unknown = set(s["fact_ids"]) - fact_ids
        if unknown:
            errs.append(f"{s['id']}: kaynaksız gerçek kimliği {sorted(unknown)}")
        for field in ("start_frame_desc", "end_frame_desc", "effects"):
            errs += [f"{s['id']}.{field}: kadın ifadesi '{w}'" for w in female_mentions(s[field])]
        errs += [f"{s['id']}.motion: kadın ifadesi '{w}'"
                 for m in s["motion"] for w in female_mentions(m["what"])]

    total = sum(s["duration_s"] for s in shots)
    if not fmt["min_duration_s"] <= total <= fmt["max_duration_s"]:
        errs.append(f"toplam süre {total} sn; {fmt['min_duration_s']}–{fmt['max_duration_s']} olmalı")

    narration = " ".join(s["narration"] for s in shots)
    words = len(narration.split())
    lo, hi = fmt["narration_words"]
    if not lo <= words <= hi:
        errs.append(f"anlatım {words} kelime; {lo}–{hi} olmalı")
    for sentence in _sentences(narration):
        if len(sentence.split()) > fmt["max_sentence_words"]:
            warns.append(f"uzun cümle ({len(sentence.split())} kelime): {sentence}")
    if not _sentences(shots[0]["narration"]) or not any(x.endswith("?") for x in _sentences(shots[0]["narration"])):
        warns.append("kanca sahnesinde soru yok")
    return errs, warns


def check_refs_cover_shots(manifest: dict, shot_ids: list[str]) -> list[str]:
    covered = {sid for ref in manifest["refs"] for sid in ref["assigned_shots"]}
    return [f"{sid}: referans görsel yok (Kural 6)" for sid in shot_ids if sid not in covered]
