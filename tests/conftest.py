"""pytest configuration and shared fixtures for HackMySkills tests."""
from __future__ import annotations

import pytest
from pathlib import Path


@pytest.fixture()
def hms_home(tmp_path, monkeypatch):
    """Isolated HMS home directory for each test.

    Monkeypatches HMS_HOME and CONFIG_PATH in hms.config so that tests
    never touch the real ~/.hackmyskills directory.

    Also initializes the Peewee DB with a fresh test.db in tmp_path,
    creates Card and ReviewHistory tables, and closes the DB after each test.
    """
    from hms.db import db
    from hms.models import Card, ReviewHistory, UserStat

    home = tmp_path / ".hackmyskills"
    home.mkdir()
    (home / "content").mkdir()

    monkeypatch.setattr("hms.config.HMS_HOME", home)
    monkeypatch.setattr("hms.config.CONFIG_PATH", home / "config.toml")
    monkeypatch.setattr("hms.init.HMS_HOME", home)

    db.init(str(home / "test.db"), pragmas={"foreign_keys": 1})
    db.create_tables([Card, ReviewHistory, UserStat], safe=True)

    yield home

    db.close()
