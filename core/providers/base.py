"""Sağlayıcı arayüzleri. Her dış servis bu arayüzlerden birini uygular.

Gerçek sağlayıcılar (fal_seedance.py, gemini_image.py, anthropic_llm.py, elevenlabs.py,
image_search.py) ve FFmpeg tabanlı renderer aynı imzaları kullanır; pipeline hangisinin
çalıştığını bilmez.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol


@dataclass
class LLMResult:
    data: dict
    input_tokens: int
    output_tokens: int


@dataclass
class ImageCandidate:
    url: str
    source: str          # wikimedia | openverse | pexels | serpapi
    license: str
    author: str
    title: str
    internal_only: bool = False  # SerpAPI sonuçları yalnızca iç referans


@dataclass
class WordTiming:
    word: str
    start: float
    end: float


@dataclass
class MediaInfo:
    duration_s: float
    width: int
    height: int
    fps: float
    has_audio: bool
    loudness_lufs: float | None = None


class LLMProvider(Protocol):
    def complete_json(self, *, task: str, prompt: str, schema: dict, images: list[Path] = (),
                      web_search: bool = False, context: dict | None = None) -> LLMResult: ...


class ImageSearchProvider(Protocol):
    def search(self, query: str, limit: int) -> list[ImageCandidate]: ...
    def download(self, candidate: ImageCandidate, dest: Path) -> Path: ...


class ImageProvider(Protocol):
    def generate(self, *, prompt: str, ref_images: list[Path], style_images: list[Path],
                 out_path: Path, aspect_ratio: str, image_size: str) -> None: ...


class VideoProvider(Protocol):
    def image_to_video(self, *, first_frame: Path, last_frame: Path, prompt: str, duration_s: int,
                       resolution: str, aspect_ratio: str, seed: int, out_path: Path,
                       generate_audio: bool = False) -> None: ...


class TTSProvider(Protocol):
    def synthesize(self, *, text: str, voice_id: str | None, out_path: Path) -> list[WordTiming]: ...


class SFXProvider(Protocol):
    def generate(self, *, prompt: str, duration_s: float, out_path: Path) -> None: ...


class Renderer(Protocol):
    """FFmpeg tarafı: ücretsiz sahneler, montaj, ölçüm."""
    def kenburns(self, *, start_frame: Path, end_frame: Path, duration_s: float, out_path: Path) -> None: ...
    def assemble(self, *, job_dir: Path, script: dict, timing: dict, shots: list[Path],
                 sfx: list[dict], out_path: Path) -> None: ...
    def thumbnail(self, *, video: Path, at_s: float, out_path: Path) -> None: ...
    def probe(self, path: Path) -> MediaInfo: ...
    def sample_frames(self, path: Path, fps: float, out_dir: Path) -> list[Path]: ...
    def music_suspected(self, path: Path) -> bool: ...


@dataclass
class Providers:
    llm: LLMProvider
    image_search: ImageSearchProvider
    image: ImageProvider
    video: VideoProvider
    tts: TTSProvider
    sfx: SFXProvider
    renderer: Renderer
    extra: dict = field(default_factory=dict)
