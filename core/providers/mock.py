"""Sahte sağlayıcılar: ücretsiz, ağ gerektirmez, her zaman aynı çıktıyı üretir.

Aşama 2'nin kabul testi ve birim testleri bunlarla çalışır. Ürettikleri dosyalar gerçek
medya değil, yer tutucudur (PNG'ler geçerli ama tek renklidir).
"""
from __future__ import annotations

import json
import math
import struct
import zlib
from pathlib import Path

from core.providers.base import (
    ImageCandidate, LLMResult, MediaInfo, Providers, WordTiming,
)

WORDS_PER_SECOND = 170 / 60
SENTENCE_GAP_S = 0.25


def solid_png(width: int = 9, height: int = 16, rgb: tuple[int, int, int] = (21, 23, 27)) -> bytes:
    def chunk(kind: bytes, data: bytes) -> bytes:
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)
    row = b"\x00" + bytes(rgb) * width
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(row * height)) + chunk(b"IEND", b""))


def _write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


_NUM = ["one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven"]
_BEATS = [1, 2, 3, 4, 4, 4, 4, 4, 4, 5, 6]
_DURATIONS = [5, 4, 4, 4, 4, 5, 4, 4, 3, 5, 4]
_IMPORTANCE = ["high", "low", "medium", "medium", "high", "high", "high", "medium", "medium", "medium", "high"]
_REFS = {1: ["exterior"], 2: ["assembled_component"], 3: ["assembled_component", "cutaway"],
         4: ["cutaway", "detail_parts"], 5: ["drivetrain_chain"], 6: ["exterior"]}


def _frame_desc(device: str, i: int) -> str:
    return (f"Unbranded {device}, stage {i} of the explanation. Visible parts: one outer housing in dark grey "
            f"cast iron at the center of the frame; one polished steel shaft running left to right through the "
            f"middle; four light silver aluminium components spaced evenly along the shaft; section faces solid "
            f"orange. Camera 1.5 m away at shaft height, 35 mm lens, subject fills the central 60% of the frame. "
            f"No people anywhere in the scene.")


def mock_script(idea: dict, fact_ids: list[str]) -> dict:
    shots = []
    for i, beat in enumerate(_BEATS):
        narration = ("What happens inside this machine when it starts working?" if i == 0
                     else f"Shot {_NUM[i]} shows how this part of the machine moves.")
        dur = _DURATIONS[i]
        shots.append({
            "id": f"S{i + 1:02d}", "title": f"Stage {i + 1}", "beat": beat, "duration_s": dur,
            "narration": narration,
            "start_keyframe": f"K{i:02d}", "end_keyframe": f"K{i + 1:02d}",
            "start_frame_desc": _frame_desc(idea["device"], i),
            "end_frame_desc": _frame_desc(idea["device"], i + 1),
            "camera_move": {"from": f"camera position {i}", "path": "slow dolly-in of 0.3 m, no rotation",
                            "to": f"camera position {i + 1}", "speed": "slow", "easing": "ease-in-out"},
            "motion": [{"t0": 0.0, "t1": float(dur),
                        "what": "the shaft rotates clockwise at a steady speed; all other parts stay still"}],
            "effects": "light-blue air particles flow from left to right" if beat == 4 else "",
            "overlay_label": {"n": f"STEP {i - 2:02d} / 06", "t": "MECHANISM"} if beat == 4 else None,
            "hud": "20:1" if i == 5 else None,
            "sfx": [{"t": 0.2, "prompt": "low steady mechanical hum, steel, close-up, 2s"}],
            "refs_needed": _REFS[beat],
            "fact_ids": fact_ids[:1] if beat == 4 else [],
            "motion_importance": _IMPORTANCE[i],
        })
    narration_full = " ".join(s["narration"] for s in shots)
    return {
        "job_id": "", "title": idea["title"], "total_duration_s": sum(_DURATIONS),
        "narration_full": narration_full, "shots": shots,
        "title_yt": idea["title"][:60], "description_yt": f"{idea['title']}. Sources below.",
        "tags": ["shorts", "howitworks", "engineering"],
        "pinned_comment": "What machine should we open up next?",
    }


class MockLLM:
    def __init__(self, fail_qc: dict[str, int] | None = None):
        # fail_qc: {"K03": 1} → K03 ilk kontrolde bir kez kalır (yeniden deneme testi için)
        self.fail_qc = dict(fail_qc or {})
        self.calls: list[str] = []

    def complete_json(self, *, task, prompt, schema, images=(), web_search=False, context=None) -> LLMResult:
        context = context or {}
        self.calls.append(task)
        if task == "research":
            data = {
                "facts": [
                    {"id": "f1", "claim": "The compression ratio is about 16 to 1.", "value": "16:1", "unit": None,
                     "sources": [{"url": "https://example.org/a", "title": "Source A"},
                                 {"url": "https://example.org/b", "title": "Source B"}],
                     "confidence": "high"},
                    {"id": "f2", "claim": "The crankshaft converts up-and-down motion into rotation.",
                     "value": None, "unit": None,
                     "sources": [{"url": "https://example.org/c", "title": "Source C"}], "confidence": "high"},
                ],
                "components": [
                    {"name": "crankshaft", "count": 1, "material": "forged steel", "position": "bottom",
                     "motion": "rotates clockwise"},
                ],
            }
            return LLMResult(data, 3000, 1500)
        if task == "script":
            return LLMResult(mock_script(context["idea"], context["fact_ids"]), 6000, 5000)
        if task == "ref_score":
            return LLMResult({"scores": [{"index": i, "score": 9.0 - 0.1 * i, "reason": "clear, relevant"}
                                         for i in range(len(images))]}, 1500 * max(1, len(images)), 300)
        if task == "visual_qc":
            target = context.get("target", "")
            if self.fail_qc.get(target, 0) > 0:
                self.fail_qc[target] -= 1
                return LLMResult({"pass": False, "scores": {k: 6 for k in _QC_KEYS}, "fatal": [],
                                  "problems": ["injector is off-center"],
                                  "fix_instructions": "Place the injector exactly on the cylinder axis."}, 2000, 300)
            return LLMResult({"pass": True, "scores": {k: 9 for k in _QC_KEYS}, "fatal": [], "problems": [],
                              "fix_instructions": ""}, 2000, 300)
        raise ValueError(f"MockLLM bilinmeyen görev: {task}")


_QC_KEYS = ["technical_accuracy", "physical_logic", "continuity", "people", "text_logos", "realism", "composition"]


class MockImageSearch:
    def search(self, query: str, limit: int) -> list[ImageCandidate]:
        slug = query.replace(" ", "-")
        return [ImageCandidate(url=f"https://example.org/{slug}/{i}.jpg", source="wikimedia",
                               license="CC BY 4.0", author=f"Author {i}", title=f"{query} {i}")
                for i in range(limit)]

    def download(self, candidate: ImageCandidate, dest: Path) -> Path:
        _write(dest, solid_png(rgb=(90, 90, 90)))
        return dest


class MockImage:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, *, prompt, ref_images, style_images, out_path, aspect_ratio, image_size) -> None:
        self.prompts.append(prompt)
        _write(out_path, solid_png())


class MockVideo:
    def __init__(self):
        self.requests: list[dict] = []

    def image_to_video(self, *, first_frame, last_frame, prompt, duration_s, resolution, aspect_ratio, seed,
                       out_path, generate_audio=False) -> None:
        self.requests.append({"duration_s": duration_s, "resolution": resolution, "seed": seed,
                              "generate_audio": generate_audio, "prompt": prompt})
        _write(out_path, b"MOCK-MP4")


class MockTTS:
    def synthesize(self, *, text, voice_id, out_path) -> list[WordTiming]:
        words, t = [], 0.0
        for token in text.split():
            dur = 1 / WORDS_PER_SECOND
            words.append(WordTiming(token, round(t, 3), round(t + dur * 0.9, 3)))
            t += dur + (SENTENCE_GAP_S if token[-1] in ".?!" else 0)
        _write(out_path, b"MOCK-MP3")
        return words


class MockSFX:
    def __init__(self):
        self.prompts: list[str] = []

    def generate(self, *, prompt, duration_s, out_path) -> None:
        self.prompts.append(prompt)
        _write(out_path, b"MOCK-WAV")


class MockRenderer:
    def __init__(self, fmt: dict):
        self.fmt = fmt

    def kenburns(self, *, start_frame, end_frame, duration_s, out_path) -> None:
        _write(out_path, b"MOCK-KENBURNS")

    def assemble(self, *, job_dir, script, timing, shots, sfx, out_path) -> None:
        _write(out_path, b"MOCK-FINAL")
        meta = {"duration_s": timing["total_s"], "width": self.fmt["width"], "height": self.fmt["height"],
                "fps": self.fmt["fps"], "has_audio": True, "loudness_lufs": -14.0}
        out_path.with_suffix(".mock.json").write_text(json.dumps(meta), encoding="utf-8")

    def thumbnail(self, *, video, at_s, out_path) -> None:
        _write(out_path, solid_png())

    def probe(self, path: Path) -> MediaInfo:
        meta = json.loads(path.with_suffix(".mock.json").read_text(encoding="utf-8"))
        return MediaInfo(**meta)

    def sample_frames(self, path: Path, fps: float, out_dir: Path) -> list[Path]:
        frames = []
        n = max(1, math.ceil(self.probe(path).duration_s * fps)) if path.with_suffix(".mock.json").exists() else 2
        for i in range(n):
            frame = out_dir / f"f{i:04d}.png"
            _write(frame, solid_png())
            frames.append(frame)
        return frames

    def music_suspected(self, path: Path) -> bool:
        return False


def build(config: dict, fail_qc: dict[str, int] | None = None) -> Providers:
    return Providers(llm=MockLLM(fail_qc), image_search=MockImageSearch(), image=MockImage(),
                     video=MockVideo(), tts=MockTTS(), sfx=MockSFX(), renderer=MockRenderer(config["format"]))
