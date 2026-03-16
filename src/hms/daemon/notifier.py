"""Desktop notification sender for HackMySkills daemon."""
from __future__ import annotations

import sys
from pathlib import Path

from hms.config import HMS_HOME

# Path to the helper bat file that 'hms interrupt' is launched from.
_INTERRUPT_BAT: Path = HMS_HOME / "interrupt.bat"


def _ensure_bat() -> Path:
    """Create (or overwrite) the interrupt.bat helper next to the PID file.

    The bat file is the launch target for notification click actions —
    Windows WinRT can open a file path but not an arbitrary argv.
    """
    _INTERRUPT_BAT.parent.mkdir(parents=True, exist_ok=True)
    _INTERRUPT_BAT.write_text("@echo off\nhms interrupt\npause\n")
    return _INTERRUPT_BAT


def _open_interrupt_terminal() -> None:
    """Spawn a new console window running 'hms interrupt'.

    Falls back to subprocess if called outside the notification click path.
    """
    import subprocess

    subprocess.Popen(
        ["cmd.exe", "/k", "hms", "interrupt"],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


def send_notification(question_preview: str) -> None:
    """Send a Windows toast notification.

    Clicking the notification (or the 'Start Review' button) opens a new
    terminal running ``hms interrupt``.

    Args:
        question_preview: Short text shown as the notification body.
    """
    if sys.platform != "win32":
        return  # winotify is Windows-only; silently skip on other platforms

    from winotify import Notification

    bat_path = str(_ensure_bat())

    toast = Notification(
        app_id="HackMySkills",
        title="Time to review!",
        msg=question_preview,
        duration="short",
        launch=bat_path,
    )
    toast.add_actions(label="Start Review", launch=bat_path)
    toast.show()
