---
phase: 04-interrupt-daemon
plan: "00"
subsystem: daemon
tags: [apscheduler, desktop-notifier, psutil, abc, platform, scaffolding, tdd, xfail]

requires:
  - phase: 03-gamification-adaptive-difficulty
    provides: UserStat model, gamification module, scheduler.py patterns

provides:
  - src/hms/daemon/ importable package with docstring stubs for start/stop/status
  - DaemonPlatform ABC with 4 abstract methods (register_startup, unregister_startup, spawn_detached, is_running)
  - hms.daemon.platform.get_platform() OS detection factory
  - tests/test_daemon.py with 11 strict xfail stubs covering INT-01 through INT-06
  - pyproject.toml updated with apscheduler>=3.11,<4, desktop-notifier>=6.0, psutil>=6.0

affects:
  - 04-01 (WindowsPlatform implementation uses DaemonPlatform ABC)
  - 04-02 (DaemonController implementation depends on daemon package)
  - 04-03 (notify_job implementation depends on daemon package)

tech-stack:
  added:
    - apscheduler>=3.11,<4
    - desktop-notifier>=6.0
    - psutil>=6.0
  patterns:
    - DaemonPlatform ABC pattern for OS-specific platform abstraction
    - get_platform() lazy-import factory for Windows/macOS/Linux
    - strict xfail stubs with NotImplementedError raise pattern (established in Phase 2, continued here)

key-files:
  created:
    - src/hms/daemon/__init__.py
    - src/hms/daemon/platform/__init__.py
    - src/hms/daemon/platform/base.py
    - tests/test_daemon.py
  modified:
    - pyproject.toml

key-decisions:
  - "DaemonPlatform ABC uses 4 abstract methods: register_startup, unregister_startup, spawn_detached, is_running — covers full lifecycle"
  - "get_platform() uses lazy imports (inside if/elif/else branches) to avoid ImportError on platforms where winreg/WinRT are absent"
  - "apscheduler pinned to >=3.11,<4 to avoid APScheduler 4.x breaking API changes"

patterns-established:
  - "Platform abstraction: DaemonPlatform ABC + get_platform() factory in platform/__init__.py"
  - "xfail strict stubs: raise NotImplementedError, not just pass — reason is explicit and suite fails if stub accidentally passes"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05, INT-06]

duration: 2min
completed: 2026-03-16
---

# Phase 04 Plan 00: Interrupt Daemon Wave 0 Scaffolding Summary

**importable hms.daemon package, DaemonPlatform ABC with 4 abstract methods, 11 strict xfail stubs for INT-01 through INT-06, and three new runtime dependencies added to pyproject.toml**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T02:55:35Z
- **Completed:** 2026-03-16T02:57:36Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments

- Added apscheduler, desktop-notifier, and psutil runtime dependencies with correct version constraints
- Created daemon package skeleton (3 files): daemon/__init__.py, daemon/platform/__init__.py, daemon/platform/base.py
- DaemonPlatform ABC established as the interface all Wave 1 platform implementations will satisfy
- 11 strict xfail stubs cover all 6 INT requirements; full suite remains green (73 passed, 11 xfailed)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add daemon dependencies to pyproject.toml** - `60c33ff` (chore)
2. **Task 2: Create daemon package skeleton and DaemonPlatform ABC** - `3895786` (feat)
3. **Task 3: Create tests/test_daemon.py with xfail stubs** - `71db051` (test)

## Files Created/Modified

- `pyproject.toml` - Added apscheduler>=3.11,<4, desktop-notifier>=6.0, psutil>=6.0 to dependencies
- `src/hms/daemon/__init__.py` - Package init with public API docstring (start/stop/status stubs)
- `src/hms/daemon/platform/__init__.py` - OS detection factory get_platform() with lazy imports per platform
- `src/hms/daemon/platform/base.py` - DaemonPlatform ABC: register_startup, unregister_startup, spawn_detached, is_running
- `tests/test_daemon.py` - 11 strict xfail stubs covering INT-01 through INT-06 (plus INT-04b traceability)

## Decisions Made

- apscheduler pinned to >=3.11,<4 (not open-ended) to prevent accidental adoption of APScheduler 4.x which has breaking API changes
- get_platform() uses lazy imports inside if/elif/else blocks — avoids ImportError on platforms without winreg or WinRT available at import time
- DaemonPlatform ABC covers exactly 4 lifecycle operations matching the Windows implementation spec from research

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Wave 0 scaffolding complete; all Wave 1-2 plans (04-01, 04-02, 04-03) can proceed
- WindowsPlatform in 04-01 implements DaemonPlatform ABC, filling the concrete class stub
- Blockers from STATE.md still apply: Windows WinRT notification permission flow needs validation before 04-03 implements notify_job

---
*Phase: 04-interrupt-daemon*
*Completed: 2026-03-16*

## Self-Check: PASSED

All files present: pyproject.toml, src/hms/daemon/__init__.py, src/hms/daemon/platform/__init__.py, src/hms/daemon/platform/base.py, tests/test_daemon.py, 04-00-SUMMARY.md
All commits present: 60c33ff, 3895786, 71db051
