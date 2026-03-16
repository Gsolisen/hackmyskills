"""Tests for src/hms/daemon/ — interrupt daemon (Phase 4).

Covers: INT-01 through INT-06.
All tests are xfail stubs until Wave 1-2 implementations are complete.
"""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# INT-01: DaemonController.start() — PID file + startup registration
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_start_writes_pid(hms_home):
    """DaemonController.start() spawns detached process and writes daemon.pid."""
    raise NotImplementedError


@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_spawn_detached(hms_home):
    """WindowsPlatform.spawn_detached() creates process with DETACHED_PROCESS flags."""
    raise NotImplementedError


@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_startup_registration(hms_home):
    """WindowsPlatform.register_startup() writes HKCU\\Run key with correct value."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-02: DaemonController.stop() — terminate + unregister
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_stop_removes_pid(hms_home):
    """DaemonController.stop() reads PID, terminates process, removes daemon.pid."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-03: notify_job() fires within work hours and under daily cap
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_notify_job_fires(hms_home):
    """notify_job() calls notifier.send() when within work hours and cap not reached."""
    raise NotImplementedError


@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_scheduler_fires(hms_home):
    """AsyncIOScheduler is configured with interval trigger id=hms_interrupt replace_existing=True."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-04: notification click spawns terminal; hms interrupt runs 1-card session
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_interrupt_terminal_spawn(hms_home):
    """_open_interrupt_terminal() calls subprocess.Popen with cmd.exe /k hms interrupt."""
    raise NotImplementedError


@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_interrupt_session(hms_home):
    """run_session is called with max_cards=1 when notify_job triggers."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-05: quiet hours — _is_within_work_hours() returns False outside window
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_quiet_hours(hms_home):
    """_is_within_work_hours() returns False when current time is outside work window."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-06: daily cap respected — notify_job skips when cap is hit
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_cap_respected(hms_home):
    """notify_job() does not call notifier.send() when today's review count >= daily_cap."""
    raise NotImplementedError


# ---------------------------------------------------------------------------
# INT-04b: hms interrupt CLI command (test_cli.py covers this — stub here for traceability)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(reason="not yet implemented", strict=True)
def test_interrupt_command(hms_home):
    """hms interrupt CLI command invokes run_session with max_cards=1."""
    raise NotImplementedError
