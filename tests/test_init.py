"""Tests for first-run initialization (FOUND-02). Stubs for Plan 01-02."""
import pytest


@pytest.mark.xfail(reason="hms.init not yet created — will be implemented in Plan 01-02")
def test_first_run_creates_db(hms_home):
    from hms.init import ensure_initialized
    ensure_initialized()
    assert (hms_home / "data.db").exists()


@pytest.mark.xfail(reason="hms.init not yet created — will be implemented in Plan 01-02")
def test_first_run_creates_content_dir(hms_home):
    from hms.init import ensure_initialized
    ensure_initialized()
    assert (hms_home / "content").is_dir()
