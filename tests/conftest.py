import copy
from pathlib import Path

import pytest

from core import settings
from core.app import App
from core.providers import mock


@pytest.fixture
def config():
    return copy.deepcopy(settings.load_config())


@pytest.fixture
def make_app(tmp_path: Path, config):
    def _make(providers=None, cfg=None, clock=None) -> App:
        cfg = cfg or config
        app = App.open(config=cfg, data_root=tmp_path, providers=providers or mock.build(cfg), clock=clock)
        app.sync_ideas()
        return app
    return _make
