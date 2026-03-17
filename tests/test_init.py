"""Tests for first-run initialization (FOUND-02)."""


def test_first_run_creates_db(hms_home):
    from hms.init import ensure_initialized
    ensure_initialized()
    assert (hms_home / "data.db").exists()


def test_first_run_creates_content_dir(hms_home):
    from hms.init import ensure_initialized
    ensure_initialized()
    assert (hms_home / "content").is_dir()


def test_first_run_writes_config(hms_home):
    from hms.init import ensure_initialized
    ensure_initialized()
    assert (hms_home / "config.toml").exists()


def test_first_run_idempotent(hms_home):
    """Re-running ensure_initialized() must not raise."""
    from hms.init import ensure_initialized
    ensure_initialized()
    ensure_initialized()
    assert (hms_home / "data.db").exists()


def test_config_toml_documented(hms_home):
    """EXT-02: config.toml has inline comments for every setting."""
    import tomllib
    from hms.init import ensure_initialized
    from hms.config import DEFAULT_CONFIG
    ensure_initialized()
    config_path = hms_home / "config.toml"
    content = config_path.read_text()
    # Must contain comments (lines starting with #)
    comment_lines = [l for l in content.splitlines() if l.strip().startswith("#")]
    assert len(comment_lines) >= 10, f"Only {len(comment_lines)} comment lines, need >= 10"
    # Must parse as valid TOML
    parsed = tomllib.loads(content)
    # Must contain all top-level keys from DEFAULT_CONFIG
    assert "daily_cap" in parsed, "Missing daily_cap"
    assert "interval_minutes" in parsed, "Missing interval_minutes"
    assert "quiet_hours" in parsed, "Missing quiet_hours section"
    assert "daemon" in parsed, "Missing daemon section"
    # Daemon section must have all keys
    assert "interval_minutes" in parsed["daemon"], "Missing daemon.interval_minutes"
    assert "work_hours_start" in parsed["daemon"], "Missing daemon.work_hours_start"
    assert "work_hours_end" in parsed["daemon"], "Missing daemon.work_hours_end"
    assert "daily_cap" in parsed["daemon"], "Missing daemon.daily_cap"
