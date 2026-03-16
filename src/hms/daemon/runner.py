"""Daemon entry point for HackMySkills.

Run as:  pythonw.exe -m hms.daemon.runner

Starts a BackgroundScheduler (interval trigger, 90-min default) that fires
send_notification() via notify_job(). Writes its PID to
~/.hackmyskills/daemon.pid on startup. Removes the PID file on clean shutdown.
"""
from __future__ import annotations

import signal
import threading

from apscheduler.schedulers.background import BackgroundScheduler

from hms.config import load_config
from hms.daemon.controller import PID_FILE, write_pid
from hms.daemon.scheduler import notify_job
from hms.init import ensure_initialized


def daemon_main() -> None:
    """Entry point for the interrupt daemon.

    Initialises HMS, writes PID, starts the APScheduler with an interval
    trigger, then blocks on a threading Event. On Windows, psutil.terminate()
    from DaemonController.stop() kills the process directly.
    """
    ensure_initialized()
    write_pid()

    cfg = load_config()
    daemon_cfg = cfg.get("daemon", {})
    interval_minutes = daemon_cfg.get("interval_minutes", 90)

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        notify_job,
        "interval",
        minutes=interval_minutes,
        id="hms_interrupt",
        replace_existing=True,
    )
    scheduler.start()

    stop_event = threading.Event()

    def _handle_signal(signum: int, frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGINT, _handle_signal)
    signal.signal(signal.SIGTERM, _handle_signal)

    try:
        stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    daemon_main()
