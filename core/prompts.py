"""Prompt dosyalarını yükler ve Bölüm 7 şablonlarına göre doldurur.

Prompt metinleri channels/<kanal>/prompts/ altındadır; burada yalnızca birleştirme yapılır.
"""
from __future__ import annotations

import json
import re
from pathlib import Path


def load(channel_dir: Path, channel: dict, name: str) -> str:
    return (channel_dir / "prompts" / channel["prompts"][name]).read_text(encoding="utf-8").strip()


def fill(template: str, **values: object) -> str:
    """{anahtar} alanlarını doldurur; şablondaki diğer süslü parantezlere dokunmaz."""
    for key, value in values.items():
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        template = template.replace("{" + key + "}", text)
    return template


def learnings(channel_dir: Path) -> list[str]:
    """learnings.md içindeki "- " ile başlayan maddeler (Bölüm 10.2, madde 8)."""
    path = channel_dir / "learnings.md"
    if not path.exists():
        return []
    return [line[2:].strip() for line in path.read_text(encoding="utf-8").splitlines() if line.startswith("- ")]


def with_learnings(prompt: str, rules: list[str]) -> str:
    if not rules:
        return prompt
    return prompt + "\n\nLESSONS FROM PREVIOUS REVIEWS (always follow):\n" + "\n".join(f"- {r}" for r in rules)


def first_sentence(text: str) -> str:
    return re.split(r"(?<=\.)\s+", text.strip(), maxsplit=1)[0].rstrip(".")


def keyframe_prompt(*, channel: dict, forbidden: str, kf_id: str, which: str, shot: dict,
                    frame_desc: str, refs: list[dict], prev_kf: str | None,
                    lessons: list[str], fix_notes: list[str] = ()) -> str:
    """Bölüm 7.3: 9 başlığın tamamı doldurulur."""
    style = channel["style"]
    camera = shot["camera_move"]["from" if which == "start" else "to"]
    ref_lines = "\n".join(f"  Image {i} = {r['description']}" for i, r in enumerate(refs, 1))
    colors = "; ".join(f"{k.replace('_', ' ')} {v}" for k, v in style["color_code"].items())
    continuity = (f"Must match the previous keyframe {prev_kf} exactly in camera, lighting and part design "
                  f"(attached as style image)." if prev_kf else
                  "First keyframe of the video: establishes the design, lighting and camera for all later frames.")
    parts = [
        f"[1 PURPOSE] Keyframe {kf_id} of a photoreal vertical 9:16 technical Short. "
        f"This is the {which} frame of shot {shot['id']}: \"{shot['title']}\".",
        "[2 REFERENCES] Use the attached images as ground truth for shape, proportions and part layout:\n"
        f"{ref_lines}\n"
        "  Style images = channel look (lighting, colors, orange section faces). Match their look, not their content.\n"
        "  Do NOT copy any reference literally. Do NOT invent parts that the references and the component list do not show.",
        f"[3 SUBJECT] {frame_desc}",
        f"[4 COMPOSITION] {camera}. {style['composition_safe_zones']}",
        f"[5 LIGHTING] {style['lighting']}",
        f"[6 MATERIALS & COLOR CODE] Materials exactly as listed in SUBJECT. Color code: {colors}.",
        f"[7 CONTINUITY] {continuity}",
        f"[8 PHOTOREALISM] {style['photorealism']}",
    ]
    if lessons:
        parts.append("[LESSONS] " + " ".join(lessons))
    if fix_notes:
        parts.append("[FIX FROM PREVIOUS ATTEMPT] " + " ".join(fix_notes))
    parts.append(f"[9 FORBIDDEN] {forbidden}")
    return "\n".join(parts)


def shot_prompt(*, forbidden: str, shot: dict, n_shots: int, duration_s: int,
                start_desc: str, end_desc: str, fix_notes: list[str] = ()) -> str:
    """Bölüm 7.4: Seedance image-to-video promptu."""
    cam = shot["camera_move"]
    shake = "" if "shake" in cam["path"].lower() else ", no shake"
    motion = "\n".join(f"  {m['t0']:.1f}-{m['t1']:.1f}s: {m['what']}" for m in shot["motion"])
    parts = [
        f"[SHOT] {shot['id']} of {n_shots}, {duration_s}s, vertical 9:16, photoreal, continuous single take, no cuts.",
        f"[START] The video begins exactly on the provided first frame: {first_sentence(start_desc)}.",
        f"[END] The video ends exactly on the provided last frame: {first_sentence(end_desc)}.",
        f"[CAMERA] {cam['from']} -> {cam['path']} -> {cam['to']}. Speed: {cam['speed']}, smooth {cam['easing']}{shake}.",
        f"[MOTION — in this exact order]\n{motion}",
    ]
    if shot["effects"]:
        parts.append(f"[PARTICLES/EFFECTS] {shot['effects']}")
    parts.append("[KEEP CONSTANT] Same design, part count, materials, lighting and background as the first and "
                 "last frame. Nothing appears or disappears unless stated.")
    if fix_notes:
        parts.append("[FIX FROM PREVIOUS ATTEMPT] " + " ".join(fix_notes))
    parts.append(f"[FORBIDDEN] {forbidden}")
    return "\n".join(parts)
