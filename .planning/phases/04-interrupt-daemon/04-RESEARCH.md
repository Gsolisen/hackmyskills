# Phase 4: Interrupt Daemon - Research

**Researched:** 2026-03-15
**Domain:** Background daemon process, Windows desktop notifications, APScheduler, process lifecycle management
**Confidence:** MEDIUM-HIGH

---

## Summary

Phase 4 introduces the highest-risk component in the HackMySkills v1 build: a background daemon process that fires desktop notifications on a schedule and opens a one-question terminal session on click. The risk comes from three distinct hard problems on Windows: (1) spawning a truly detached process that survives the parent's exit, (2) WinRT notification delivery requiring a running asyncio event loop in the daemon, and (3) Windows Startup folder / registry registration.

The decision to use APScheduler 3.x (stable, `BackgroundScheduler` or `BlockingScheduler`) + `desktop-notifier 6.x` (async, WinRT-backed) is already locked. APScheduler 4.x is still pre-release and must NOT be used. The daemon process runs `asyncio.run()` as its main loop because `desktop-notifier` demands a live event loop for click callbacks; APScheduler's `AsyncIOScheduler` integrates cleanly into that same loop.

**Primary recommendation:** The daemon script's main loop must be an asyncio event loop. Use `AsyncIOScheduler` (not `BlockingScheduler`) so both the scheduler and `desktop-notifier` share the same loop. Spawn the daemon via `pythonw.exe` with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` flags so it runs without a console window and survives the CLI parent's exit.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| INT-01 | `hms daemon start` launches background APScheduler process and registers in Windows Startup folder | APScheduler AsyncIOScheduler + subprocess DETACHED_PROCESS spawn + winreg/Startup folder registration |
| INT-02 | `hms daemon stop` cleanly stops the daemon and removes from Startup folder | PID file read + psutil.Process.terminate() + winreg delete key |
| INT-03 | Daemon sends desktop notification at configurable intervals during work hours | APScheduler interval trigger + desktop-notifier async send + work-hours time range check |
| INT-04 | Notification click (or `hms interrupt`) opens 1-question mini-session in terminal | desktop-notifier `on_clicked` callback + subprocess.Popen to spawn `cmd.exe /k hms interrupt` |
| INT-05 | Quiet hours configurable in config.toml (no notifications before 09:00 or after 21:00) | Existing `load_config()` already has `quiet_hours` defaults; daemon reads config at job fire time |
| INT-06 | Daemon respects daily card cap — stops sending interrupts once daily cap is hit | `build_queue()` length check from quiz.py; query daily reviewed count against cap before sending notification |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| APScheduler | 3.11.2 (3.x branch) | Interval-based job scheduling inside daemon process | Stable, production-ready; 4.x is pre-release and must NOT be used |
| desktop-notifier | 6.2.0 | Cross-platform desktop notifications with click callbacks | Already in stack decision; WinRT-backed on Windows |
| psutil | 6.x | Cross-platform process lookup by PID and clean terminate | Standard for PID-based process management; avoids os.kill limitations on Windows |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| winreg (stdlib) | built-in | Windows registry startup registration | `DaemonPlatform.register_startup()` on Windows |
| asyncio (stdlib) | built-in | Event loop for desktop-notifier callbacks | Required — desktop-notifier is async-only |
| subprocess (stdlib) | built-in | Spawn detached daemon process; spawn terminal for interrupt | `DaemonPlatform.spawn_detached()` and notification click handler |
| pathlib (stdlib) | built-in | PID file read/write at `~/.hackmyskills/daemon.pid` | Clean cross-platform file handling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| APScheduler 3.x | APScheduler 4.x | 4.x is pre-release (4.0.0a6), no migration path, breaks backwards compat — NOT suitable for production |
| psutil | os.kill / taskkill subprocess | os.kill(pid, 0) works for existence check on Windows; psutil.terminate() is more robust and cross-platform |
| winreg registry key | Startup folder .lnk shortcut | winreg HKCU Run key is simpler (no shell32 dependency); Startup folder needs pywin32/winshell for .lnk creation |

**Installation:**
```bash
pip install "apscheduler>=3.11,<4" "desktop-notifier>=6.0" "psutil>=6.0"
```

---

## Architecture Patterns

### Recommended Module Structure
```
src/hms/daemon/
├── __init__.py          # exports DaemonController
├── controller.py        # DaemonController: start/stop/status logic, PID file
├── runner.py            # daemon entry point: asyncio.run(daemon_main())
├── scheduler.py         # build_notify_schedule(), quiet hours check, cap check
├── notifier.py          # send_notification(), terminal spawn on click
└── platform/
    ├── __init__.py
    ├── base.py          # DaemonPlatform ABC: spawn_detached, register_startup, unregister_startup
    ├── windows.py       # WindowsPlatform — DETACHED_PROCESS, winreg
    ├── linux.py         # LinuxPlatform stub — NotImplementedError
    └── macos.py         # MacOSPlatform stub — NotImplementedError
```

### Pattern 1: AsyncIO Daemon Main Loop

**What:** The daemon entry point runs `asyncio.run(daemon_main())`. Inside, `AsyncIOScheduler` is started and a `stop_event` is awaited indefinitely. The scheduler fires `notify_job()` as a regular coroutine on the asyncio loop.

**When to use:** Any time `desktop-notifier` callbacks must fire — the library requires a live event loop.

**Example:**
```python
# Source: APScheduler 3.x docs + desktop-notifier README pattern
import asyncio
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from desktop_notifier import DesktopNotifier

notifier = DesktopNotifier(app_name="HackMySkills")

async def daemon_main():
    stop_event = asyncio.Event()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_job,
        "interval",
        minutes=interval_minutes,
        id="hms_interrupt",
        replace_existing=True,
    )
    scheduler.start()

    # Graceful shutdown on SIGTERM (Windows: handle via signal module)
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except NotImplementedError:
            pass  # Windows does not support add_signal_handler for all signals

    await stop_event.wait()
    scheduler.shutdown(wait=False)

asyncio.run(daemon_main())
```

### Pattern 2: Detached Process Spawn (Windows)

**What:** `hms daemon start` spawns `pythonw.exe -m hms.daemon.runner` with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP` flags. `pythonw.exe` is used instead of `python.exe` to avoid a console window popping up.

**When to use:** INT-01. The spawning process (the CLI) exits immediately; the daemon continues independently.

**Example:**
```python
# Source: Python subprocess docs + Windows process creation flags
import subprocess
import sys
from pathlib import Path

DETACHED = 0x00000008  # DETACHED_PROCESS
NEW_GROUP = 0x00000200  # CREATE_NEW_PROCESS_GROUP

def spawn_detached(cmd: list[str]) -> int:
    """Spawn cmd as a detached Windows process. Returns child PID."""
    proc = subprocess.Popen(
        cmd,
        creationflags=DETACHED | NEW_GROUP,
        close_fds=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    return proc.pid

def get_pythonw() -> str:
    """Return path to pythonw.exe alongside the current python.exe."""
    return str(Path(sys.executable).parent / "pythonw.exe")
```

### Pattern 3: Windows Startup Registration via winreg

**What:** Write a `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run` registry value named `HackMySkills` pointing to the daemon launch command.

**When to use:** INT-01 / INT-02. No pywin32 or shell32 dependency needed.

**Example:**
```python
# Source: winreg stdlib docs
import winreg

REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
REG_VALUE_NAME = "HackMySkills"

def register_startup(cmd_str: str) -> None:
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        winreg.SetValueEx(key, REG_VALUE_NAME, 0, winreg.REG_SZ, cmd_str)

def unregister_startup() -> None:
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, REG_KEY, 0, winreg.KEY_SET_VALUE
        ) as key:
            winreg.DeleteValue(key, REG_VALUE_NAME)
    except FileNotFoundError:
        pass  # already removed
```

### Pattern 4: Notification Click Opens Terminal

**What:** The `on_clicked` callback in `desktop-notifier` is a plain callable. On Windows, spawn `cmd.exe /k hms interrupt` in a new console window.

**When to use:** INT-04.

**Example:**
```python
# Source: desktop-notifier README async pattern
import asyncio
import subprocess
from desktop_notifier import DesktopNotifier

notifier = DesktopNotifier(app_name="HackMySkills")

def _open_interrupt_terminal() -> None:
    subprocess.Popen(
        ["cmd.exe", "/k", "hms", "interrupt"],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

async def send_notification(question_preview: str) -> None:
    await notifier.send(
        title="Time to review!",
        message=question_preview,
        on_clicked=_open_interrupt_terminal,
    )
```

### Pattern 5: PID File Lifecycle

**What:** On startup, write `os.getpid()` to `~/.hackmyskills/daemon.pid`. On stop, read the PID, call `psutil.Process(pid).terminate()`, then delete the file.

**When to use:** INT-01 / INT-02.

**Example:**
```python
from pathlib import Path
import os, psutil

PID_FILE = Path.home() / ".hackmyskills" / "daemon.pid"

def write_pid() -> None:
    PID_FILE.write_text(str(os.getpid()))

def read_pid() -> int | None:
    try:
        return int(PID_FILE.read_text().strip())
    except (FileNotFoundError, ValueError):
        return None

def stop_daemon() -> bool:
    pid = read_pid()
    if pid is None:
        return False
    try:
        psutil.Process(pid).terminate()
        PID_FILE.unlink(missing_ok=True)
        return True
    except psutil.NoSuchProcess:
        PID_FILE.unlink(missing_ok=True)
        return False
```

### Pattern 6: Quiet Hours and Cap Check

**What:** Inside `notify_job()`, check current time against `work_hours_start`/`work_hours_end` from config, and count today's reviews against `daily_cap` before sending. This logic runs inside the daemon (which has DB access).

**When to use:** INT-05 / INT-06.

**Example:**
```python
from datetime import datetime, time
from hms.config import load_config
from hms.models import ReviewHistory

def _is_within_work_hours(cfg: dict) -> bool:
    now = datetime.now().time()
    start = time.fromisoformat(cfg.get("work_hours_start", "09:00"))
    end = time.fromisoformat(cfg.get("work_hours_end", "21:00"))
    return start <= now <= end

def _daily_reviews_today(cfg: dict) -> int:
    today = datetime.now().date()
    return ReviewHistory.select().where(
        ReviewHistory.reviewed_at >= datetime(today.year, today.month, today.day)
    ).count()

async def notify_job() -> None:
    cfg = load_config()
    if not _is_within_work_hours(cfg):
        return
    if _daily_reviews_today(cfg) >= cfg.get("daily_cap", 25):
        return
    # pick a question preview and send notification
    ...
```

### Pattern 7: `hms interrupt` Mini-Session

**What:** `hms interrupt` calls `run_session()` with `max_cards=1`. The existing `run_session` already handles a queue of 1 card — no new session logic needed, just a `daily_cap=1` call to `build_queue`.

**When to use:** INT-04.

**Example:**
```python
# In cli.py — new @app.command()
@app.command()
def interrupt() -> None:
    """Run a single-question interrupt session."""
    from hms.init import ensure_initialized
    from hms import quiz as quiz_module
    ensure_initialized()
    quiz_module.run_session(max_cards=1)
```

Note: `run_session` currently reads `daily_cap` from config. The interrupt command needs to override it to 1. The cleanest approach is a `max_cards` parameter on `run_session` (currently only `daily_cap` from config). This is a small, contained extension.

### Typer Sub-App Pattern for `hms daemon`

The current `cli.py` has a stub `daemon()` command. Replace it with a `daemon_app = typer.Typer()` sub-app with `start`, `stop`, and `status` subcommands, then `app.add_typer(daemon_app, name="daemon")`.

```python
# Source: Typer docs — SubCommands
daemon_app = typer.Typer(help="Manage the background interrupt daemon.")

@daemon_app.command()
def start() -> None: ...

@daemon_app.command()
def stop() -> None: ...

@daemon_app.command()
def status() -> None: ...

app.add_typer(daemon_app, name="daemon")
```

### Anti-Patterns to Avoid

- **Using `BlockingScheduler` in the daemon:** BlockingScheduler blocks the main thread — the asyncio event loop for desktop-notifier callbacks never runs. Use `AsyncIOScheduler` exclusively.
- **Running `python.exe` for the daemon:** This opens a visible console window. Use `pythonw.exe` on Windows.
- **APScheduler 4.x:** Still pre-release (4.0.0a6). The API is completely different from 3.x and has no stable migration path. Pin to `<4`.
- **Writing PID before `asyncio.run()`:** Write the PID inside the `daemon_main()` coroutine after the event loop is established, not before `asyncio.run()` — this ensures the PID is the actual daemon process, not a transient launcher.
- **Adding jobs without `replace_existing=True`:** APScheduler with a persistent job store will duplicate the job on every daemon restart. Always pass `id=` and `replace_existing=True`.
- **Skipping `close_fds=True` and DEVNULL redirects in spawn:** Without these, the child inherits open file handles that can cause resource leaks or block parent process cleanup.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Interval scheduling | Custom `time.sleep()` loop with drift | APScheduler `AsyncIOScheduler` interval trigger | Handles coalescing, missed fires, persistent job store, clean shutdown |
| Desktop notifications | win10toast, ctypes WinRT calls | desktop-notifier 6.x | Cross-platform abstraction, click callbacks, WinRT bridge already solved |
| Process existence check | `os.kill(pid, 0)` + try/except on Windows | `psutil.Process(pid).is_running()` | `os.kill` has inconsistent behavior on Windows; psutil handles zombie processes correctly |
| Startup registration | Startup folder `.lnk` shortcut via win32com | winreg `HKCU\Run` key | No shell32/pywin32 dependency; simpler, more reliable |

---

## Common Pitfalls

### Pitfall 1: desktop-notifier callbacks never fire
**What goes wrong:** Notifications appear but clicking them does nothing.
**Why it happens:** `desktop-notifier` requires the asyncio event loop to remain running. If the daemon uses `BlockingScheduler` or `time.sleep()` as its main loop, the event loop has already exited.
**How to avoid:** The daemon's main loop MUST be `await stop_event.wait()` inside `asyncio.run()`. Use `AsyncIOScheduler`.
**Warning signs:** Notification sent successfully (no error) but `on_clicked` is never called.

### Pitfall 2: APScheduler duplicate jobs on daemon restart
**What goes wrong:** After each restart, an extra copy of the notification job accumulates in the SQLite job store. Notifications fire multiple times per interval.
**Why it happens:** `scheduler.add_job()` without `id=` and `replace_existing=True` inserts a new row each time.
**How to avoid:** Always pass `id="hms_interrupt"` and `replace_existing=True`.
**Warning signs:** Multiple rapid notifications; job store DB growing.

### Pitfall 3: Daemon process visible console window
**What goes wrong:** A black cmd.exe window flashes or stays open when the daemon starts.
**Why it happens:** The daemon was spawned with `python.exe` instead of `pythonw.exe`, or without `DETACHED_PROCESS` flag.
**How to avoid:** `get_pythonw()` resolves `pythonw.exe` next to `sys.executable`. Use `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`.
**Warning signs:** Console window appears on daemon start.

### Pitfall 4: WinRT notification permission not granted
**What goes wrong:** `desktop-notifier` sends no notification and no error is raised; notifications simply do not appear.
**Why it happens:** Windows 11 has per-app notification permissions. First run may require the user to allow notifications from "Python" (or custom app_name) in Windows Settings > Notifications.
**How to avoid:** Document the first-run permission step. Use a recognizable `app_name` in `DesktopNotifier(app_name="HackMySkills")`.
**Warning signs:** No notification appears but no exception is raised — desktop-notifier silently drops notifications when denied.

### Pitfall 5: Daemon DB access conflict
**What goes wrong:** SQLite `OperationalError: database is locked` when both the daemon and `hms quiz` run concurrently.
**Why it happens:** SQLite WAL mode is not enabled by default in Peewee; concurrent writes from two processes block.
**How to avoid:** Enable WAL mode pragma: `db.init(str(db_path), pragmas={"foreign_keys": 1, "journal_mode": "wal"})`. The daemon only reads (checking daily cap) and occasionally writes review history (interrupt session) — WAL handles this safely.
**Warning signs:** Occasional `OperationalError: database is locked` in daemon logs or quiz session.

### Pitfall 6: Signal handling on Windows asyncio
**What goes wrong:** `loop.add_signal_handler(signal.SIGTERM, ...)` raises `NotImplementedError` on Windows.
**Why it happens:** Windows does not fully support POSIX signal handlers in asyncio.
**How to avoid:** Wrap `add_signal_handler` in a `try/except NotImplementedError`. Use PID-based termination from `hms daemon stop` (psutil.terminate sends OS-level signal that kills the process directly without needing the handler).
**Warning signs:** `NotImplementedError` at daemon startup on Windows.

### Pitfall 7: `run_session` needs `max_cards` parameter
**What goes wrong:** `hms interrupt` starts a full session (up to daily_cap cards) instead of exactly 1 card.
**Why it happens:** `run_session` currently reads `daily_cap` from config and builds the full queue.
**How to avoid:** Add an optional `max_cards: int | None = None` parameter to `run_session`. When set, use `min(daily_cap, max_cards)` as the effective cap. This is a single-line change to `quiz.py`.
**Warning signs:** Running `hms interrupt` drains all due cards.

---

## Code Examples

### Full Daemon Runner Skeleton
```python
# Source: APScheduler 3.x userguide + desktop-notifier README
# src/hms/daemon/runner.py
import asyncio
import os
import signal
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from desktop_notifier import DesktopNotifier
from hms.config import load_config
from hms.daemon.controller import PID_FILE, write_pid
from hms.init import ensure_initialized

notifier = DesktopNotifier(app_name="HackMySkills")

async def daemon_main() -> None:
    ensure_initialized()
    write_pid()
    cfg = load_config()

    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        notify_job,
        "interval",
        minutes=cfg.get("interval_minutes", 90),
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
            pass  # Windows

    try:
        await stop_event.wait()
    finally:
        scheduler.shutdown(wait=False)
        PID_FILE.unlink(missing_ok=True)

if __name__ == "__main__":
    asyncio.run(daemon_main())
```

### Config Extension (config.toml `[daemon]` section)
```toml
# ~/.hackmyskills/config.toml
daily_cap = 25

[daemon]
interval_minutes = 90
work_hours_start = "09:00"
work_hours_end = "21:00"
```

The existing `load_config()` already uses `tomllib` — the `[daemon]` subsection is automatically available as `cfg["daemon"]` after `config.update(user_config)`.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| win10toast for Windows notifications | desktop-notifier 6.x (WinRT) | 2023-2024 | win10toast unmaintained; desktop-notifier has async click callbacks |
| APScheduler 3.x `BlockingScheduler` for pure scheduler scripts | `AsyncIOScheduler` when asyncio is needed | APScheduler 3.3+ | Avoids thread-pool overhead when the job function itself is async |
| Double-fork daemon on Unix | `start_new_session=True` in subprocess.Popen (cross-platform) | Python 3.2+ | Simpler; Windows-compatible (though DETACHED_PROCESS is more explicit for our use case) |

**Deprecated/outdated:**
- `win10toast` / `win10toast-click`: No longer maintained; do NOT use.
- APScheduler 4.x: Pre-release only; API breaks backwards compat; do NOT use in production.
- Startup folder `.lnk` shortcut via pywin32/winshell: Heavier dependency than winreg; avoid unless `.lnk` is specifically required.

---

## Open Questions

1. **WinRT first-run permission flow**
   - What we know: desktop-notifier silently drops notifications when Windows notification permission is denied. The library uses the app_name as the identity.
   - What's unclear: Whether a fresh Python install on Windows 11 requires the user to manually grant notification permission in Settings, or whether it's auto-granted.
   - Recommendation: Implement a `hms daemon status` command that sends a test notification and reports success/failure. Document the permission step in the `hms daemon start` output.

2. **SQLite WAL mode — existing DB migration**
   - What we know: The DB is already initialized in Phase 1 without WAL mode pragma. The daemon adds a second concurrent reader/writer.
   - What's unclear: Whether the existing DB needs a migration to enable WAL, or whether setting the pragma at connection time is sufficient.
   - Recommendation: Setting `journal_mode=wal` at connection time via Peewee pragma is sufficient — WAL mode activates on next write and is persistent in the DB file. No migration needed.

3. **`hms interrupt` daily cap counting**
   - What we know: INT-06 says the daemon stops sending interrupts once the daily cap is hit. The cap is checked based on reviews recorded today.
   - What's unclear: Whether an interrupt session should count against the main `hms quiz` daily cap or have a separate cap.
   - Recommendation: Use the same `daily_cap` from config, counting all `ReviewHistory` rows from today (both quiz and interrupt). This keeps the user's total daily review load predictable.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` `[tool.pytest.ini_options]` |
| Quick run command | `pytest tests/test_daemon.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| INT-01 | `DaemonController.start()` writes PID file and calls `platform.register_startup()` | unit (mock spawn + winreg) | `pytest tests/test_daemon.py::test_start_writes_pid -x` | Wave 0 |
| INT-02 | `DaemonController.stop()` reads PID, calls terminate, removes PID file, calls unregister | unit (mock psutil + winreg) | `pytest tests/test_daemon.py::test_stop_removes_pid -x` | Wave 0 |
| INT-03 | `notify_job()` calls `notifier.send()` when within work hours and cap not hit | unit (mock notifier + DB) | `pytest tests/test_daemon.py::test_notify_job_fires -x` | Wave 0 |
| INT-04 | `_open_interrupt_terminal()` spawns `cmd.exe /k hms interrupt` | unit (mock subprocess.Popen) | `pytest tests/test_daemon.py::test_interrupt_terminal_spawn -x` | Wave 0 |
| INT-05 | `_is_within_work_hours()` returns False outside configured window | unit (mock datetime.now) | `pytest tests/test_daemon.py::test_quiet_hours -x` | Wave 0 |
| INT-06 | `notify_job()` skips notification when today's review count >= daily_cap | unit (mock DB query) | `pytest tests/test_daemon.py::test_cap_respected -x` | Wave 0 |
| INT-04b | `hms interrupt` CLI command runs a 1-card session | unit (mock run_session, assert max_cards=1) | `pytest tests/test_cli.py::test_interrupt_command -x` | Wave 0 |

Note: The actual daemon process lifecycle (spawn, survive reboot, WinRT notification delivery) is **manual-only** — these behaviors require a real Windows environment and cannot be automated in unit tests.

### Sampling Rate
- **Per task commit:** `pytest tests/test_daemon.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_daemon.py` — covers INT-01 through INT-06 unit tests
- [ ] `src/hms/daemon/__init__.py` — package init
- [ ] Framework already installed (`pytest>=8.0` in dev dependencies)

---

## Sources

### Primary (HIGH confidence)
- [APScheduler 3.x user guide](https://apscheduler.readthedocs.io/en/3.x/userguide.html) — BackgroundScheduler, AsyncIOScheduler, SQLAlchemy job store, interval trigger, `replace_existing` pattern
- [desktop-notifier 6.2.0 docs](https://desktop-notifier.readthedocs.io/en/latest/) — async API, `on_clicked` callback, event loop requirements
- [desktop-notifier PyPI](https://pypi.org/project/desktop-notifier/) — current version 6.2.0, Windows WinRT dependency
- [Python subprocess docs](https://docs.python.org/3/library/subprocess.html) — `DETACHED_PROCESS`, `CREATE_NEW_PROCESS_GROUP`, `CREATE_NEW_CONSOLE`
- [Python winreg stdlib](https://docs.python.org/3/library/winreg.html) — registry key write/delete for startup registration
- Existing codebase: `src/hms/config.py`, `src/hms/quiz.py`, `src/hms/cli.py` — integration points verified by direct read

### Secondary (MEDIUM confidence)
- [APScheduler PyPI](https://pypi.org/project/APScheduler/) — confirmed 3.11.2 is current stable; 4.x pre-release warning
- [desktop-notifier GitHub README](https://github.com/samschott/desktop-notifier) — pywinrt dependency confirmed, sync module exists, daemon event loop pattern
- WebSearch: Windows DETACHED_PROCESS + CREATE_NEW_PROCESS_GROUP combination verified across multiple sources
- WebSearch: winreg `HKCU\Run` as simpler alternative to Startup folder shortcut

### Tertiary (LOW confidence — flag for validation)
- WinRT notification permission flow on first run: no official documentation found; behavior needs hands-on validation on Windows 11
- SQLite WAL mode + daemon concurrent access: recommendation based on SQLite documentation patterns, not tested in this specific Peewee setup

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — APScheduler 3.x stable, desktop-notifier 6.2.0 on PyPI, psutil standard practice
- Architecture: HIGH — patterns derived from official docs and existing codebase structure
- Windows process spawning: MEDIUM — DETACHED_PROCESS pattern well-documented; pythonw.exe path resolution needs validation
- WinRT notification permissions: LOW — silently drops notifications; behavior on fresh installs unverified

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (APScheduler 4.x GA could change recommendations if released)
