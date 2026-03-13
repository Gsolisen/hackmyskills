"""pytest configuration and shared fixtures for HackMySkills tests."""
from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture()
def hms_home(tmp_path, monkeypatch):
    """Isolated HMS home directory for each test.

    Monkeypatches HMS_HOME and CONFIG_PATH in hms.config so that tests
    never touch the real ~/.hackmyskills directory.

    Note: db init/close will be added to this fixture in Plan 01-02
    when hms.db exists. For now, the fixture provides isolation only.
    """
    home = tmp_path / ".hackmyskills"
    home.mkdir()
    (home / "content").mkdir()
    monkeypatch.setattr("hms.config.HMS_HOME", home)
    monkeypatch.setattr("hms.config.CONFIG_PATH", home / "config.toml")
    yield home
