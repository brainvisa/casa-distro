# -*- coding: utf-8 -*-

import pytest


@pytest.fixture(autouse=True)
def isolate_from_home(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CASA_BASE_DIRECTORY", raising=False)
