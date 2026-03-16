"""Abstract base class for OS-specific daemon platform operations."""
from __future__ import annotations

from abc import ABC, abstractmethod


class DaemonPlatform(ABC):
    """Abstract interface for OS-specific daemon lifecycle operations.

    Concrete implementations:
      - platform/windows.py: WindowsPlatform (winreg + DETACHED_PROCESS)
      - platform/linux.py: LinuxPlatform (stub — raises NotImplementedError)
      - platform/macos.py: MacOSPlatform (stub — raises NotImplementedError)
    """

    @abstractmethod
    def register_startup(self, cmd_str: str) -> None:
        """Register cmd_str to run at OS login/startup."""

    @abstractmethod
    def unregister_startup(self) -> None:
        """Remove the startup registration (idempotent — no error if absent)."""

    @abstractmethod
    def spawn_detached(self, cmd: list[str]) -> int:
        """Spawn cmd as a detached process. Returns the child PID."""

    @abstractmethod
    def is_running(self, pid: int) -> bool:
        """Return True if a process with pid is currently running."""
