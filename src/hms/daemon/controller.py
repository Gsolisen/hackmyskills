"""Daemon lifecycle controller for HackMySkills.

Handles start/stop/status by managing a PID file at ~/.hackmyskills/daemon.pid
and delegating OS-specific operations to the platform layer.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import psutil

from hms.config import HMS_HOME

PID_FILE: Path = HMS_HOME / "daemon.pid"


def write_pid() -> None:
    """Write current process PID to PID_FILE. Called from inside daemon_main()."""
    PID_FILE.parent.mkdir(parents=True, exist_ok=True)
    PID_FILE.write_text(str(os.getpid()))


def read_pid() -> int | None:
    """Read PID from PID_FILE. Returns None if file is absent or invalid."""
    try:
        return int(PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None


class DaemonController:
    """High-level start/stop/status operations for the interrupt daemon."""

    def start(self) -> None:
        """Spawn the daemon process and register it in the Windows Startup folder.

        Uses pythonw.exe (no console window) with DETACHED_PROCESS |
        CREATE_NEW_PROCESS_GROUP flags so the daemon survives the CLI parent's exit.
        The startup registration command matches what the daemon runner expects.
        """
        from hms.daemon.platform import get_platform
        from hms.daemon.platform.windows import _get_pythonw

        platform = get_platform()
        pythonw = _get_pythonw()
        cmd = [pythonw, "-m", "hms.daemon.runner"]
        pid = platform.spawn_detached(cmd)
        # Register the same command for Windows Startup
        cmd_str = f'"{pythonw}" -m hms.daemon.runner'
        platform.register_startup(cmd_str)
        # PID written by daemon_main() itself after event loop starts
        # but store it here too so status() works immediately
        PID_FILE.parent.mkdir(parents=True, exist_ok=True)
        PID_FILE.write_text(str(pid))

    def stop(self) -> bool:
        """Terminate the daemon and remove it from startup registration.

        Returns True if a running process was found and terminated,
        False if the daemon was already stopped.
        """
        from hms.daemon.platform import get_platform

        platform = get_platform()
        pid = read_pid()
        terminated = False

        if pid is not None:
            try:
                psutil.Process(pid).terminate()
                terminated = True
            except psutil.NoSuchProcess:
                pass  # already gone
        PID_FILE.unlink(missing_ok=True)
        platform.unregister_startup()
        return terminated

    def status(self) -> str:
        """Return 'running' if daemon PID file exists and process is alive, else 'stopped'."""
        from hms.daemon.platform import get_platform

        platform = get_platform()
        pid = read_pid()
        if pid is not None and platform.is_running(pid):
            return "running"
        return "stopped"
