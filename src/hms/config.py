"""Configuration reader for HackMySkills."""
from __future__ import annotations

import tomllib
from pathlib import Path

HMS_HOME: Path = Path.home() / ".hackmyskills"
CONFIG_PATH: Path = HMS_HOME / "config.toml"

DEFAULT_CONFIG: dict = {
    "daily_cap": 25,
    "quiet_hours": {
        "start": "09:00",
        "end": "21:00",
    },
    "interval_minutes": 90,
}


def load_config() -> dict:
    """Load configuration from CONFIG_PATH, falling back to defaults.

    Reads config.toml with tomllib if the file exists, then merges over
    DEFAULT_CONFIG so that missing keys get their default values.
    Returns the merged configuration dictionary.
    """
    config = dict(DEFAULT_CONFIG)
    if CONFIG_PATH.exists():
        with CONFIG_PATH.open("rb") as f:
            user_config = tomllib.load(f)
        config.update(user_config)
    return config
