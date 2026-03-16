---
phase: 04-interrupt-daemon
plan: "03"
subsystem: cli
tags: [typer, apscheduler, psutil, desktop-notifier, winreg, mocking]

# Dependency graph
requires:
  - phase: 04-interrupt-daemon
    provides: DaemonController, scheduler, notifier, runner from plans 04-00 through 04-02

provides:
  - daemon_app Typer sub-app (start/stop/status) wired into hms CLI
  - interrupt command calling run_session(max_cards=1)
  - All 11 xfail daemon test stubs converted to passing unit tests
  - test_interrupt_command in test_cli.py

affects: [05-content-generation, future CLI extensions]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Typer sub-app pattern: daemon_app = typer.Typer(); app.add_typer(daemon_app, name='daemon')
    - Lazy import inside command functions to avoid circular imports and platform errors
    - Patching hms.models.Card.select (not Card) to avoid MagicMock field descriptor comparison errors
    - Patching hms.daemon.notifier.send_notification for async scheduler tests

key-files:
  created:
    - tests/test_daemon.py (full rewrite — 11 real passing tests replacing xfail stubs)
  modified:
    - src/hms/cli.py (daemon_app sub-app with start/stop/status; interrupt command)
    - tests/test_cli.py (added test_interrupt_command)

key-decisions:
  - "Patch Card.select not Card class — patching the whole model class makes Card.due a MagicMock, breaking <= comparison with datetime in scheduler.py"
  - "test_interrupt_session delegates conceptually to test_interrupt_command in test_cli.py — kept in test_daemon.py as a send_notification call assertion to cover the notify_job path"
  - "Windows-only tests (spawn_detached, startup_registration) guarded with pytest.mark.skipif(sys.platform != 'win32') to run on this machine but not fail on Linux CI"

patterns-established:
  - "Typer sub-app pattern: daemon_app + app.add_typer — reusable for future CLI groupings"
  - "Async coroutine testing: asyncio.run() with patch context managers for APScheduler jobs"
  - "Platform-guarded tests: skipif(sys.platform != 'win32') for Windows-specific code"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05, INT-06]

# Metrics
duration: 15min
completed: 2026-03-16
---

# Phase 4 Plan 03: CLI Wiring and Test Conversion Summary

**Typer daemon sub-app (start/stop/status) and interrupt command wired into hms CLI; all 11 xfail test stubs converted to passing unit tests using mocks**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-16T03:10:00Z
- **Completed:** 2026-03-16T03:25:00Z
- **Tasks:** 2 auto tasks complete (Task 3 is human-verify checkpoint)
- **Files modified:** 3

## Accomplishments
- Replaced daemon() stub in cli.py with a full daemon_app Typer sub-app exposing start/stop/status subcommands
- Added interrupt() command that calls run_session(max_cards=1) — closes the notification → terminal → quiz loop
- Converted all 11 xfail stubs in test_daemon.py to real passing unit tests (INT-01 through INT-06)
- Added test_interrupt_command to test_cli.py confirming max_cards=1 call via CliRunner
- Full suite: pytest tests/ -x -q exits 0 (85 tests, 0 failures, 0 xfail)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire CLI daemon sub-app and interrupt command** - `506732a` (feat)
2. **Task 2: Convert xfail stubs to passing unit tests** - `d692ed8` (test)

**Plan metadata:** (to be added after checkpoint completes)

## Files Created/Modified
- `src/hms/cli.py` - Added daemon_app sub-app (start/stop/status) and interrupt command; removed daemon() stub
- `tests/test_daemon.py` - Full rewrite: 11 real passing tests with mocks for all INT-01..INT-06 behaviors
- `tests/test_cli.py` - Added test_interrupt_command verifying run_session called with max_cards=1

## Decisions Made
- Patching `hms.models.Card.select` rather than the full `Card` class avoids MagicMock field descriptor issues where `Card.due <= datetime` raises TypeError
- test_interrupt_session kept in test_daemon.py as a send_notification assertion to trace the scheduler → notifier path; the CLI-level assertion lives in test_cli.py
- Windows-only tests guarded with `pytest.mark.skipif(sys.platform != "win32")` for CI compatibility

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong patch targets in async scheduler tests**
- **Found during:** Task 2 (xfail stub conversion)
- **Issue:** Initial patches for `ensure_initialized`, `load_config`, and `Card` used wrong module paths (scheduler module doesn't have them at top level — they're imported inside the coroutine). Patching `Card` entirely caused MagicMock `<=` TypeError.
- **Fix:** Changed patches to `hms.init.ensure_initialized`, `hms.config.load_config`, and `hms.models.Card.select` respectively
- **Files modified:** tests/test_daemon.py
- **Verification:** All 11 tests pass after fix
- **Committed in:** d692ed8 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (Rule 1 — wrong patch targets, corrected inline)
**Impact on plan:** Purely a testing correction. No behavior changes to production code.

## Issues Encountered
- Async scheduler tests required careful patch target selection due to lazy imports inside `notify_job()` coroutine. Resolved by patching at the module that owns the object, not where it's used.

## User Setup Required
None - no external service configuration required for Tasks 1-2.

**Pending human verification (Task 3 checkpoint):** User must verify:
1. pip install -e ".[dev]" installs apscheduler, desktop-notifier, psutil
2. pytest tests/ -v — all PASSED, no xfail
3. hms interrupt — single card session runs
4. hms daemon start/stop/status lifecycle
5. Windows toast notification fires after ~60s with interval_minutes=1
6. Registry Run key present after start, absent after stop

## Next Phase Readiness
- Full daemon implementation complete pending human notification verification
- Phase 5 (content generation) can proceed independently of WinRT notification confirmation
- Blocker: Windows notification permission grant may be needed on first run (Pitfall 4 in 04-RESEARCH.md)

---
*Phase: 04-interrupt-daemon*
*Completed: 2026-03-16*

## Self-Check: PASSED
