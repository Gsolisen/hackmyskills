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
