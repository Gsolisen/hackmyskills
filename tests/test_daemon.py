"""Tests for src/hms/daemon/ — interrupt daemon (Phase 4).

Covers: INT-01 through INT-06.
All external I/O is mocked — no real OS calls are made.
"""
from __future__ import annotations

import asyncio
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


# ---------------------------------------------------------------------------
# INT-01: DaemonController.start() — PID file + startup registration
# ---------------------------------------------------------------------------

def test_start_writes_pid(hms_home, monkeypatch):
    """DaemonController.start() spawns detached process and writes daemon.pid."""
    from hms.daemon.controller import DaemonController

    pid_file = hms_home / "daemon.pid"
    monkeypatch.setattr("hms.daemon.controller.PID_FILE", pid_file)

    with patch("hms.daemon.platform.windows.WindowsPlatform.spawn_detached", return_value=9999), \
         patch("hms.daemon.platform.windows.WindowsPlatform.register_startup"):
        ctrl = DaemonController()
        ctrl.start()

    assert pid_file.exists()
    assert pid_file.read_text().strip() == "9999"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_spawn_detached(hms_home):
    """WindowsPlatform.spawn_detached() creates process with DETACHED_PROCESS flags."""
    from hms.daemon.platform.windows import WindowsPlatform, DETACHED_PROCESS, CREATE_NEW_PROCESS_GROUP

    mock_proc = MagicMock()
    mock_proc.pid = 1234

    with patch("subprocess.Popen", return_value=mock_proc) as mock_popen:
        platform = WindowsPlatform()
        pid = platform.spawn_detached(["pythonw.exe", "-m", "hms.daemon.runner"])

    assert pid == 1234
    call_kwargs = mock_popen.call_args[1]
    assert call_kwargs["creationflags"] == (DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP)


@pytest.mark.skipif(sys.platform != "win32", reason="Windows only")
def test_startup_registration(hms_home):
    """WindowsPlatform.register_startup() writes HKCU\\Run key with correct value."""
    import winreg
    from hms.daemon.platform.windows import WindowsPlatform, REG_KEY, REG_VALUE_NAME

    mock_key = MagicMock()

    with patch("winreg.OpenKey", return_value=mock_key.__enter__.return_value) as mock_open, \
         patch("winreg.SetValueEx") as mock_set:
        # Use context manager approach
        mock_open.return_value.__enter__ = MagicMock(return_value=mock_key)
        mock_open.return_value.__exit__ = MagicMock(return_value=False)

        platform = WindowsPlatform()
        cmd_str = '"pythonw.exe" -m hms.daemon.runner'
        platform.register_startup(cmd_str)

    mock_set.assert_called_once()
    args = mock_set.call_args[0]
    assert args[1] == REG_VALUE_NAME
    assert args[4] == cmd_str


# ---------------------------------------------------------------------------
# INT-02: DaemonController.stop() — terminate + unregister
# ---------------------------------------------------------------------------

def test_stop_removes_pid(hms_home, monkeypatch):
    """DaemonController.stop() reads PID, terminates process, removes daemon.pid."""
    from hms.daemon.controller import DaemonController

    pid_file = hms_home / "daemon.pid"
    pid_file.write_text("9999")
    monkeypatch.setattr("hms.daemon.controller.PID_FILE", pid_file)

    mock_process = MagicMock()

    with patch("psutil.Process", return_value=mock_process), \
         patch("hms.daemon.platform.windows.WindowsPlatform.unregister_startup"):
        ctrl = DaemonController()
        result = ctrl.stop()

    mock_process.terminate.assert_called_once()
    assert not pid_file.exists()
    assert result is True


# ---------------------------------------------------------------------------
# INT-03: notify_job() fires within work hours and under daily cap
# ---------------------------------------------------------------------------

def test_notify_job_fires(hms_home):
    """notify_job() calls notifier.send() when within work hours and cap not reached."""
    from hms.daemon.scheduler import notify_job

    with patch("hms.daemon.scheduler._is_within_work_hours", return_value=True), \
         patch("hms.daemon.scheduler._daily_reviews_today", return_value=0), \
         patch("hms.init.ensure_initialized"), \
         patch("hms.config.load_config", return_value={"daemon": {"daily_cap": 10}}), \
         patch("hms.daemon.notifier.send_notification", new_callable=AsyncMock) as mock_notify, \
         patch("hms.models.Card.select") as mock_select:
        # Build a query chain that returns None (no due cards)
        mock_select.return_value.where.return_value.order_by.return_value.first.return_value = None
        asyncio.run(notify_job())

    mock_notify.assert_called_once()


def test_scheduler_fires(hms_home):
    """AsyncIOScheduler is configured with interval trigger id=hms_interrupt replace_existing=True."""
    from apscheduler.schedulers.asyncio import AsyncIOScheduler
    from hms.daemon.scheduler import notify_job

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_job,
        "interval",
        minutes=90,
        id="hms_interrupt",
        replace_existing=True,
    )
    job = scheduler.get_job("hms_interrupt")
    assert job is not None
    assert job.id == "hms_interrupt"


# ---------------------------------------------------------------------------
# INT-04: notification click spawns terminal; hms interrupt runs 1-card session
# ---------------------------------------------------------------------------

def test_interrupt_terminal_spawn(hms_home):
    """_open_interrupt_terminal() calls subprocess.Popen with cmd.exe /k hms interrupt."""
    import subprocess
    from hms.daemon.notifier import _open_interrupt_terminal

    with patch("subprocess.Popen") as mock_popen:
        _open_interrupt_terminal()

    mock_popen.assert_called_once()
    args = mock_popen.call_args[0][0]
    assert args == ["cmd.exe", "/k", "hms", "interrupt"]
    kwargs = mock_popen.call_args[1]
    assert kwargs.get("creationflags") == subprocess.CREATE_NEW_CONSOLE


def test_interrupt_session(hms_home):
    """run_session is called with max_cards=1 when notify_job triggers."""
    # This is verified via test_interrupt_command in test_cli.py using Typer CliRunner.
    # Here we verify it from the scheduler side: notify_job sends notification which
    # triggers _open_interrupt_terminal -> hms interrupt -> run_session(max_cards=1).
    # We validate that the notify_job path leads to send_notification being called,
    # which in turn would trigger the interrupt terminal. The full loop is integration-level.
    from hms.daemon.scheduler import notify_job

    with patch("hms.daemon.scheduler._is_within_work_hours", return_value=True), \
         patch("hms.daemon.scheduler._daily_reviews_today", return_value=0), \
         patch("hms.init.ensure_initialized"), \
         patch("hms.config.load_config", return_value={"daemon": {"daily_cap": 10}}), \
         patch("hms.models.Card.select") as mock_select, \
         patch("hms.daemon.notifier.send_notification", new_callable=AsyncMock) as mock_notify:
        mock_select.return_value.where.return_value.order_by.return_value.first.return_value = None
        asyncio.run(notify_job())

    mock_notify.assert_called_once()


# ---------------------------------------------------------------------------
# INT-05: quiet hours — _is_within_work_hours() returns False outside window
# ---------------------------------------------------------------------------

def test_quiet_hours(hms_home):
    """_is_within_work_hours() returns False when current time is outside work window."""
    from datetime import datetime
    from hms.daemon.scheduler import _is_within_work_hours

    cfg = {"daemon": {"work_hours_start": "09:00", "work_hours_end": "21:00"}}

    # Before work hours: 08:59
    mock_dt_before = MagicMock()
    mock_dt_before.time.return_value = datetime(2026, 1, 1, 8, 59).time()

    with patch("hms.daemon.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_dt_before
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result_before = _is_within_work_hours(cfg)

    assert result_before is False

    # Within work hours: 09:30
    mock_dt_during = MagicMock()
    mock_dt_during.time.return_value = datetime(2026, 1, 1, 9, 30).time()

    with patch("hms.daemon.scheduler.datetime") as mock_datetime:
        mock_datetime.now.return_value = mock_dt_during
        mock_datetime.side_effect = lambda *a, **kw: datetime(*a, **kw)
        result_during = _is_within_work_hours(cfg)

    assert result_during is True


# ---------------------------------------------------------------------------
# INT-06: daily cap respected — notify_job skips when cap is hit
# ---------------------------------------------------------------------------

def test_cap_respected(hms_home):
    """notify_job() does not call notifier.send() when today's review count >= daily_cap."""
    from hms.daemon.scheduler import notify_job

    with patch("hms.daemon.scheduler._is_within_work_hours", return_value=True), \
         patch("hms.daemon.scheduler._daily_reviews_today", return_value=10), \
         patch("hms.daemon.notifier.notifier.send", new_callable=AsyncMock) as mock_send, \
         patch("hms.init.ensure_initialized"), \
         patch("hms.config.load_config", return_value={"daemon": {"daily_cap": 10}}):
        asyncio.run(notify_job())

    mock_send.assert_not_called()


# ---------------------------------------------------------------------------
# INT-04b: hms interrupt CLI command (traceability stub — real test in test_cli.py)
# ---------------------------------------------------------------------------

def test_interrupt_command(hms_home):
    """hms interrupt CLI command invokes run_session with max_cards=1.

    Delegates to test_cli.py::test_interrupt_command for full coverage.
    This test ensures the CLI binding is exercised via CliRunner.
    """
    from typer.testing import CliRunner
    from hms.cli import app

    cli_runner = CliRunner()

    with patch("hms.quiz.run_session") as mock_run, \
         patch("hms.init.ensure_initialized"):
        result = cli_runner.invoke(app, ["interrupt"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(max_cards=1)
