"""OS detection for daemon platform selection."""
from __future__ import annotations
import sys
from hms.daemon.platform.base import DaemonPlatform


def get_platform() -> DaemonPlatform:
    """Return the platform implementation for the current OS."""
    if sys.platform == "win32":
        from hms.daemon.platform.windows import WindowsPlatform
        return WindowsPlatform()
    elif sys.platform == "darwin":
        from hms.daemon.platform.macos import MacOSPlatform
        return MacOSPlatform()
    else:
        from hms.daemon.platform.linux import LinuxPlatform
        return LinuxPlatform()
