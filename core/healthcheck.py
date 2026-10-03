"""Aşama 0 kabul testi: FFmpeg kurulu mu, 5 servis anahtarla yanıt veriyor mu?

Çalıştırma:  python -m core.healthcheck
Bu kontroller ücretsizdir; hiçbiri içerik üretmez.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from dataclasses import dataclass
from urllib.parse import urlparse

import anthropic
import httpx

from core.settings import load_config, load_env, secret

TIMEOUT_S = 15.0


@dataclass
class Result:
    name: str
    ok: bool
    detail: str


def check_ffmpeg() -> Result:
    missing = [exe for exe in ("ffmpeg", "ffprobe") if not shutil.which(exe)]
    if missing:
        return Result(
            "FFmpeg",
            False,
            f"{', '.join(missing)} bulunamadı. Windows: 'winget install Gyan.FFmpeg', sonra terminali yeniden aç.",
        )
    out = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, check=True).stdout
    return Result("FFmpeg", True, out.splitlines()[0])


def check_anthropic(base_url: str, model: str) -> Result:
    name = "Anthropic"
    key = secret("ANTHROPIC_API_KEY")
    if not key:
        return Result(name, False, "ANTHROPIC_API_KEY tanımlı değil")
    client = anthropic.Anthropic(api_key=key, base_url=base_url, max_retries=0, timeout=TIMEOUT_S)
    try:
        info = client.models.retrieve(model)
    except anthropic.AuthenticationError:
        return Result(name, False, "anahtar reddedildi (HTTP 401)")
    except anthropic.NotFoundError:
        return Result(name, False, f"'{model}' modeline bu hesapla erişilemiyor (HTTP 404)")
    except anthropic.APIStatusError as e:
        return Result(name, False, f"HTTP {e.status_code}: {e.message}")
    except anthropic.APIConnectionError:
        return Result(name, False, f"bağlantı kurulamadı ({urlparse(base_url).hostname})")
    return Result(name, True, f"yanıt veriyor, model: {info.display_name}")


def _http_check(name: str, key_name: str, url: str, headers: dict, params: dict | None = None) -> Result:
    if not secret(key_name):
        return Result(name, False, f"{key_name} tanımlı değil")
    try:
        r = httpx.get(url, headers=headers, params=params, timeout=TIMEOUT_S)
    except httpx.TransportError as e:
        return Result(name, False, f"bağlantı kurulamadı ({urlparse(url).hostname}): {type(e).__name__}")
    if r.status_code in (401, 403) or (r.status_code == 400 and "API_KEY_INVALID" in r.text):
        return Result(name, False, f"anahtar reddedildi (HTTP {r.status_code})")
    if r.is_success:
        return Result(name, True, "yanıt veriyor")
    return Result(name, False, f"beklenmeyen yanıt HTTP {r.status_code}: {r.text[:150]}")


def check_fal() -> Result:
    # Platform API'nin fiyat uç noktası hem anahtarı doğrular hem Aşama 1'deki fiyat tablosunu besler.
    return _http_check(
        "fal.ai",
        "FAL_KEY",
        "https://api.fal.ai/v1/models/pricing",
        {"Authorization": f"Key {secret('FAL_KEY')}"},
        {"endpoint_id": "bytedance/seedance-2.5/image-to-video"},
    )


def check_gemini() -> Result:
    return _http_check(
        "Google Gemini",
        "GEMINI_API_KEY",
        "https://generativelanguage.googleapis.com/v1beta/models",
        {"x-goog-api-key": secret("GEMINI_API_KEY") or ""},
        {"pageSize": 1},
    )


def check_elevenlabs() -> Result:
    return _http_check(
        "ElevenLabs",
        "ELEVENLABS_API_KEY",
        "https://api.elevenlabs.io/v1/models",
        {"xi-api-key": secret("ELEVENLABS_API_KEY") or ""},
    )


def check_pexels() -> Result:
    return _http_check(
        "Pexels",
        "PEXELS_API_KEY",
        "https://api.pexels.com/v1/search",
        {"Authorization": secret("PEXELS_API_KEY") or ""},
        {"query": "diesel engine", "per_page": 1},
    )


def run_all() -> list[Result]:
    load_env()
    llm = load_config()["llm"]
    return [
        check_ffmpeg(),
        check_anthropic(llm["base_url"], llm["model"]),
        check_fal(),
        check_gemini(),
        check_elevenlabs(),
        check_pexels(),
    ]


def main() -> int:
    results = run_all()
    for r in results:
        print(f"{'✅' if r.ok else '❌'} {r.name:<14} {r.detail}")
    failed = [r for r in results if not r.ok]
    print()
    print("Tüm kontroller geçti." if not failed else f"{len(failed)} kontrol başarısız.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
