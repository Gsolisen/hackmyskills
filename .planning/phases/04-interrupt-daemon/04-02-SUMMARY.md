---
phase: 04-interrupt-daemon
plan: "02"
subsystem: daemon
tags: [apscheduler, desktop-notifier, psutil, asyncio, sqlite-wal, pid-file, windows]

# Dependency graph
requires:
  - phase: 04-interrupt-daemon/04-01
    provides: DaemonPlatform ABC, WindowsPlatform, get_platform(), _get_pythonw(), daemon config defaults, max_cards in run_session
provides:
  - DaemonController with start/stop/status and PID file management
  - notify_job coroutine with quiet-hours and daily-cap guards
  - send_notification coroutine using DesktopNotifier with cmd.exe interrupt click
  - daemon_main asyncio entry point with AsyncIOScheduler id=hms_interrupt
  - WAL mode pragma at SqliteDatabase constructor level for concurrent access
affects: [04-03-interrupt-daemon, cli-daemon-commands]

# Tech tracking
tech-stack:
  added: [apscheduler 3.11.2, desktop-notifier 6.2.0, psutil 7.2.2]
  patterns: [pid-file-lifecycle, asyncio-daemon-loop, apscheduler-interval-replace-existing, notifier-click-callback]

key-files:
  created:
    - src/hms/daemon/controller.py
    - src/hms/daemon/scheduler.py
    - src/hms/daemon/notifier.py
    - src/hms/daemon/runner.py
  modified:
    - src/hms/db.py

key-decisions:
  - "WAL mode pragma added to SqliteDatabase(None) constructor as well as db.init() for defense-in-depth against concurrent daemon+quiz SQLite locks"
  - "notify_job() uses ensure_initialized() so daemon DB access is always properly set up regardless of startup order"
  - "PID written both by DaemonController.start() (for immediate status()) and by daemon_main() (accurate daemon PID after asyncio.run)"

patterns-established:
  - "Pattern: Daemon uses AsyncIOScheduler (not BlockingScheduler) so desktop-notifier click callbacks can fire on the live event loop"
  - "Pattern: Signal handlers wrapped in try/except NotImplementedError for Windows compatibility"
  - "Pattern: id='hms_interrupt' + replace_existing=True prevents duplicate APScheduler jobs across daemon restarts"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05, INT-06]

# Metrics
duration: 10min
completed: 2026-03-16
---

# Phase 4 Plan 02: Interrupt Daemon Runtime Summary

**DaemonController (PID file + platform spawn/stop), AsyncIOScheduler notify_job with quiet-hours/cap guards, DesktopNotifier send with cmd.exe click callback, and asyncio daemon_main loop — all wired; SQLite WAL mode enabled for concurrent access.**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-16T03:10:00Z
- **Completed:** 2026-03-16T03:20:00Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- DaemonController with start/stop/status methods using PID file at HMS_HOME/daemon.pid
- scheduler.py: notify_job coroutine with quiet-hours guard (_is_within_work_hours) and daily-cap guard (_daily_reviews_today); picks next due card as preview
- notifier.py: DesktopNotifier.send() with title "Time to review!" and _open_interrupt_terminal click callback spawning cmd.exe /k hms interrupt
- runner.py: daemon_main() with AsyncIOScheduler id=hms_interrupt replace_existing=True, stop_event await, SIGTERM/SIGINT handler with Windows NotImplementedError guard
- db.py: WAL mode pragma at SqliteDatabase constructor for concurrent daemon+quiz SQLite access

## Task Commits

Each task was committed atomically:

1. **Task 1: DaemonController and WAL mode** - `c4962d8` (feat)
2. **Task 2: scheduler.py, notifier.py, runner.py** - `e238c4f` (feat)

## Files Created/Modified

- `src/hms/daemon/controller.py` - DaemonController start/stop/status + PID_FILE + write_pid/read_pid
- `src/hms/daemon/scheduler.py` - notify_job, _is_within_work_hours, _daily_reviews_today
- `src/hms/daemon/notifier.py` - send_notification, _open_interrupt_terminal
- `src/hms/daemon/runner.py` - daemon_main asyncio entry point with AsyncIOScheduler
- `src/hms/db.py` - Added journal_mode=wal pragma at SqliteDatabase(None) constructor

## Decisions Made

- WAL mode pragma added at constructor level (in addition to db.init()) for double-protection against concurrent lock errors — Peewee merges pragmas so no conflict
- notify_job calls ensure_initialized() so the daemon can always access the DB even if cold-started from Windows Startup without prior CLI invocation
- PID written in both controller.start() and daemon_main() — controller.start() writes the spawned child PID immediately for instant status() response; daemon_main() overwrites with its own PID after the event loop starts (the accurate daemon PID)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Installed psutil (missing runtime dependency)**
- **Found during:** Task 1 (DaemonController import verification)
- **Issue:** psutil declared in pyproject.toml but not installed in environment
- **Fix:** `pip install psutil`
- **Files modified:** none (pip install only)
- **Verification:** `from hms.daemon.controller import DaemonController` imports successfully
- **Committed in:** c4962d8 (Task 1 commit)

**2. [Rule 3 - Blocking] Installed desktop-notifier and apscheduler (missing runtime deps)**
- **Found during:** Task 2 (daemon module import verification)
- **Issue:** desktop-notifier and apscheduler declared in pyproject.toml but not installed in environment
- **Fix:** `pip install "desktop-notifier>=6.0" "apscheduler>=3.11,<4"` — installed desktop-notifier 6.2.0, apscheduler 3.11.2, and WinRT runtime packages
- **Files modified:** none (pip install only)
- **Verification:** All daemon modules import successfully; full test suite green
- **Committed in:** e238c4f (Task 2 commit)

---

**Total deviations:** 2 auto-fixed (both Rule 3 — blocking missing deps)
**Impact on plan:** All deps were already declared in pyproject.toml; pip installs needed to activate them in the dev environment. No scope creep.

## Issues Encountered

None beyond the missing pip installs (handled as Rule 3 deviations above).

## User Setup Required

None - no external service configuration required. Note: Windows WinRT notification permission must be granted on first use (documented in research as known gap — notifications may silently drop until user allows in Windows Settings > Notifications).

## Next Phase Readiness

- All daemon runtime modules wired and importable (controller, scheduler, notifier, runner)
- Full test suite remains green (73 passed, 11 xfailed)
- Ready for 04-03: CLI daemon commands (hms daemon start/stop/status, hms interrupt) to wire the controller into the Typer app

---
*Phase: 04-interrupt-daemon*
*Completed: 2026-03-16*
