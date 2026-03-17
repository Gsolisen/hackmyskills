"""First-run initialization for HackMySkills.

ensure_initialized() is idempotent — safe to call on every startup.
It creates the directory structure, initializes the SQLite database,
copies bundled YAML content (stub until Plan 01-03), and writes a
default config.toml if absent.
"""
from __future__ import annotations

from pathlib import Path

# Import from hms.config so monkeypatch in tests overrides HMS_HOME here too.
from hms.config import HMS_HOME
from hms.db import db, initialize_db
from hms.models import Card, ReviewHistory, UserStat

_DEFAULT_CONFIG_TOML = """\
# HackMySkills Configuration
# Edit these settings to customize your learning experience.
# Lines starting with # are comments and are ignored.

# How many new cards per day. Higher = faster progress but more tiring.
# Default: 25
daily_cap = 25

# Notification interval in minutes (legacy, prefer [daemon] section below).
# Default: 90
interval_minutes = 90

[quiet_hours]
# Time window when the daemon will NOT send notifications.
# Use 24-hour format ("HH:MM").

# No notifications before this time. Default: "09:00"
start = "09:00"

# No notifications after this time. Default: "21:00"
end = "21:00"

[daemon]
# Background daemon settings for interrupt-mode notifications.

# Minutes between interrupt notifications during work hours.
# Default: 90
interval_minutes = 90

# Work hours window -- daemon only sends notifications during this time.
# Use 24-hour format ("HH:MM").
# Default: "09:00"
work_hours_start = "09:00"

# Default: "21:00"
work_hours_end = "21:00"

# Separate daily cap for interrupt-mode mini-sessions.
# Typically lower than the general daily_cap since each interrupt is 1 card.
# Default: 10
daily_cap = 10
"""


def ensure_initialized() -> None:
    """Create all required directories, initialize the DB, and write defaults.

    Safe to call multiple times (idempotent). Uses the monkeypatchable
    HMS_HOME from hms.config so tests never touch the real home directory.
    """
    # Re-read HMS_HOME at call time so monkeypatching in tests is respected.
    import hms.config as _cfg
    home: Path = _cfg.HMS_HOME

    home.mkdir(exist_ok=True)
    (home / "content").mkdir(exist_ok=True)

    db_path = home / "data.db"
    initialize_db(str(db_path))
    db.create_tables([Card, ReviewHistory, UserStat], safe=True)

    _copy_bundled_content(home / "content")
    _write_default_config(home / "config.toml")
    _sync_cards_from_yaml(home / "content")


def _sync_cards_from_yaml(content_dir: Path) -> None:
    """Create Card rows for any questions not yet in the database.

    Idempotent — uses get_or_create so existing cards are never overwritten.
    New cards have due=NULL so they appear as 'new' in the quiz queue.
    """
    from hms.loader import load_all_questions
    try:
        questions = load_all_questions(content_dir)
    except Exception:
        return
    for q in questions:
        Card.get_or_create(
            question_id=q["id"],
            defaults={
                "question_type": q.get("type", ""),
                "topic": q.get("topic", ""),
                "tier": q.get("tier", "L1"),
                "tags": ",".join(q.get("tags", [])) if isinstance(q.get("tags"), list) else str(q.get("tags", "")),
                "version_tag": q.get("version_tag", ""),
                "last_verified": q.get("last_verified", ""),
            },
        )


def _copy_bundled_content(content_dir: Path) -> None:
    """Copy bundled YAML question files to content_dir.

    Stub implementation — Plan 01-03 will add real YAML files to
    hms.content and implement the copy logic. This stub ensures no
    ImportError occurs and does nothing if the content package is empty.
    """
    try:
        from importlib.resources import files
        content_pkg = files("hms.content")
        for resource in content_pkg.iterdir():
            if resource.name.endswith(".yaml"):
                dest = content_dir / resource.name
                if not dest.exists():
                    dest.write_bytes(resource.read_bytes())
    except (TypeError, FileNotFoundError):
        # No bundled YAML files yet — Plan 01-03 will add them.
        pass


def _write_default_config(config_path: Path) -> None:
    """Write a commented default config.toml if the file does not exist."""
    if not config_path.exists():
        config_path.write_text(_DEFAULT_CONFIG_TOML, encoding="utf-8")
