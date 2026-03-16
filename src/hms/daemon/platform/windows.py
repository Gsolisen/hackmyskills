"""Windows-specific daemon platform implementation."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import psutil

from hms.daemon.platform.base import DaemonPlatform

# Windows process creation flags
DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200

# Registry key for startup registration
REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VALUE_NAME = "HackMySkills"


def _get_pythonw() -> str:
    """Return path to pythonw.exe alongside the current python.exe."""
    return str(Path(sys.executable).parent / "pythonw.exe")


class WindowsPlatform(DaemonPlatform):
    """Windows daemon platform: winreg startup + DETACHED_PROCESS spawn."""

    def register_startup(self, cmd_str: str) -> None:
        """Write HKCU\\Run value 'HackMySkills' = cmd_str."""
        import winreg
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.SetValueEx(key, REG_VALUE_NAME, 0, winreg.REG_SZ, cmd_str)

    def unregister_startup(self) -> None:
        """Delete HKCU\\Run value 'HackMySkills'. Idempotent — no error if absent."""
        import winreg
        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
            ) as key:
                winreg.DeleteValue(key, REG_VALUE_NAME)
        except FileNotFoundError:
            pass  # already removed — idempotent

    def spawn_detached(self, cmd: list[str]) -> int:
        """Spawn cmd as a detached Windows process. Returns child PID.

        Uses pythonw.exe (no console window), DETACHED_PROCESS |
        CREATE_NEW_PROCESS_GROUP flags, and DEVNULL for all standard streams.
        """
        proc = subprocess.Popen(
            cmd,
            creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
            close_fds=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
        )
        return proc.pid

    def is_running(self, pid: int) -> bool:
        """Return True if a process with pid is currently running."""
        try:
            return psutil.Process(pid).is_running()
        except psutil.NoSuchProcess:
            return False
