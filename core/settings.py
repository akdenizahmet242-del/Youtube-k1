"""Ayarların tek giriş noktası: config.yaml, kanal yapılandırması ve .env."""
from __future__ import annotations

import os
from pathlib import Path

import yaml
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent

# Bölüm 15, Aşama 0: zorunlu 5 servis.
REQUIRED_SECRETS = (
    "ANTHROPIC_API_KEY",
    "FAL_KEY",
    "GEMINI_API_KEY",
    "ELEVENLABS_API_KEY",
    "PEXELS_API_KEY",
)


def load_env(root: Path = ROOT) -> None:
    """.env dosyasını yükler. Ortamda zaten tanımlı değişkenler korunur."""
    load_dotenv(root / ".env", override=False)


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def channel_dir(channel_id: str, root: Path = ROOT) -> Path:
    return root / "channels" / channel_id


def load_channel(channel_id: str, root: Path = ROOT) -> dict:
    with open(channel_dir(channel_id, root) / "channel.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def secret(name: str) -> str | None:
    value = os.environ.get(name, "").strip()
    return value or None
