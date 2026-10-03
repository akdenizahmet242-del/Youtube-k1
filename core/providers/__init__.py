"""Sağlayıcı seçimi: config.yaml > providers.mode ("mock" | "live")."""
from __future__ import annotations

from core.providers.base import Providers


def build_providers(config: dict, mode: str | None = None) -> Providers:
    mode = mode or config["providers"]["mode"]
    if mode == "mock":
        from core.providers import mock
        return mock.build(config)
    if mode == "live":
        raise NotImplementedError(
            "Gerçek sağlayıcılar henüz eklenmedi (Aşama 1). config.yaml > providers.mode: mock kullan."
        )
    raise ValueError(f"bilinmeyen sağlayıcı modu: {mode}")
