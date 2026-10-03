"""JSON şemaları. LLM çıktıları ve job dosyaları bunlarla doğrulanır."""
from __future__ import annotations

import json
from functools import cache
from pathlib import Path

import jsonschema

_DIR = Path(__file__).parent


@cache
def load(name: str) -> dict:
    return json.loads((_DIR / f"{name}.schema.json").read_text(encoding="utf-8"))


def errors(name: str, data: object) -> list[str]:
    """Şema hatalarını okunabilir metin listesi olarak döndürür (boş liste = geçerli)."""
    validator = jsonschema.Draft202012Validator(load(name))
    return [f"{'/'.join(map(str, e.absolute_path)) or '(kök)'}: {e.message}"
            for e in sorted(validator.iter_errors(data), key=lambda e: list(e.absolute_path))]
