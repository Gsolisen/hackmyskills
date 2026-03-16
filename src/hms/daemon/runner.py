"""Daemon entry point for HackMySkills.

Run as:  pythonw.exe -m hms.daemon.runner

Starts an asyncio event loop that drives:
- AsyncIOScheduler (interval trigger, 90-min default)
- desktop-notifier callbacks (requires a live event loop)
Writes its PID to ~/.hackmyskills/daemon.pid on startup.
Removes the PID file on clean shutdown.
"""
from __future__ import annotations

import asyncio
import signal

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from hms.config import load_config
from hms.daemon.controller import PID_FILE, write_pid
from hms.daemon.scheduler import notify_job
from hms.init import ensure_initialized


async def daemon_main() -> None:
    """Async entry point for the interrupt daemon.

    Initialises HMS, writes PID, starts the APScheduler with an interval
    trigger, then awaits a stop_event. The stop_event is set by SIGTERM/SIGINT
    handlers where supported (POSIX); on Windows, psutil.terminate() kills the
    process directly so the handler may not fire.
    """
    ensure_initialized()
    write_pid()

    cfg = load_config()
    daemon_cfg = cfg.get("daemon", {})
    interval_minutes = daemon_cfg.get("interval_minutes", 90)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_job,
        "interval",
        minutes=interval_minutes,
        id="hms_interrupt",
        replace_existing=True,
    )
    scheduler.start()

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass  # Windows does not support add_signal_handler for all signals

    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        PID_FILE.unlink(missing_ok=True)


if __name__ == "__main__":
    asyncio.run(daemon_main())
