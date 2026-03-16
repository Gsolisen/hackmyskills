"""macOS daemon platform stub — not implemented in v1."""
from __future__ import annotations

from hms.daemon.platform.base import DaemonPlatform


class MacOSPlatform(DaemonPlatform):
    """macOS stub — raises NotImplementedError for all operations."""

    def register_startup(self, cmd_str: str) -> None:
        raise NotImplementedError("macOS daemon support not implemented in v1.")

    def unregister_startup(self) -> None:
        raise NotImplementedError("macOS daemon support not implemented in v1.")

    def spawn_detached(self, cmd: list[str]) -> int:
        raise NotImplementedError("macOS daemon support not implemented in v1.")

    def is_running(self, pid: int) -> bool:
        raise NotImplementedError("macOS daemon support not implemented in v1.")
