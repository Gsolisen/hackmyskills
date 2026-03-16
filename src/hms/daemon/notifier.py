"""Desktop notification sender for HackMySkills daemon."""
from __future__ import annotations

import subprocess

from desktop_notifier import DesktopNotifier

notifier = DesktopNotifier(app_name="HackMySkills")


def _open_interrupt_terminal() -> None:
    """Spawn a new console window running 'hms interrupt'.

    Called as the on_clicked callback for desktop notifications.
    Uses CREATE_NEW_CONSOLE so the window opens in the foreground.
    """
    subprocess.Popen(
        ["cmd.exe", "/k", "hms", "interrupt"],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )


async def send_notification(question_preview: str) -> None:
    """Send a desktop notification with the given question preview text.

    Clicking the notification calls _open_interrupt_terminal() which opens
    a new terminal running 'hms interrupt'.

    Args:
        question_preview: Short text preview shown as the notification body.
    """
    await notifier.send(
        title="Time to review!",
        message=question_preview,
        on_clicked=_open_interrupt_terminal,
    )
