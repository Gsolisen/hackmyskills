---
phase: 04-interrupt-daemon
plan: "03"
subsystem: cli
tags: [typer, apscheduler, psutil, winotify, winreg, mocking]

# Dependency graph
requires:
  - phase: 04-interrupt-daemon
    provides: DaemonController, scheduler, notifier, runner from plans 04-00 through 04-02

provides:
  - daemon_app Typer sub-app (start/stop/status) wired into hms CLI
  - interrupt command calling run_session(max_cards=1)
  - All 11 xfail daemon test stubs converted to passing unit tests
  - test_interrupt_command in test_cli.py
  - winotify-based notification with bat-file click target (replaced desktop-notifier)
  - Sync notify_job + BackgroundScheduler (replaced async notify_job + AsyncIOScheduler)

affects: [05-content-generation, future CLI extensions]

# Tech tracking
tech-stack:
  added: [winotify]
  removed: [desktop-notifier]
  patterns:
    - Typer sub-app pattern: daemon_app = typer.Typer(); app.add_typer(daemon_app, name='daemon')
    - Lazy import inside command functions to avoid circular imports and platform errors
    - Patching hms.models.Card.select (not Card) to avoid MagicMock field descriptor comparison errors
    - winotify bat-file launch target for notification click actions (WinRT can open file paths, not arbitrary argv)
    - Sync BackgroundScheduler with threading.Event for daemon lifecycle (simpler than asyncio)

key-files:
  created:
    - tests/test_daemon.py (full rewrite -- 11 real passing tests replacing xfail stubs)
  modified:
    - src/hms/cli.py (daemon_app sub-app with start/stop/status; interrupt command)
    - tests/test_cli.py (added test_interrupt_command)
    - src/hms/daemon/notifier.py (replaced desktop-notifier with winotify + bat-file click target)
    - src/hms/daemon/runner.py (BackgroundScheduler + threading.Event replaces AsyncIOScheduler + asyncio)
    - src/hms/daemon/scheduler.py (notify_job now sync, calls send_notification directly)
    - pyproject.toml (winotify replaces desktop-notifier in deps)

key-decisions:
  - "Replaced desktop-notifier with winotify -- desktop-notifier WinRT click callbacks don't fire for unpackaged Python apps on Windows"
  - "Notification click uses bat-file launch target (_ensure_bat creates interrupt.bat) -- Windows can open file paths but not arbitrary argv from toast actions"
  - "notify_job became sync, runner uses BackgroundScheduler with threading.Event -- asyncio event loop no longer needed since winotify is synchronous"
  - "Patch Card.select not Card class -- patching the whole model class makes Card.due a MagicMock, breaking <= comparison with datetime in scheduler.py"
  - "test_interrupt_session delegates conceptually to test_interrupt_command in test_cli.py -- kept in test_daemon.py as a send_notification call assertion to cover the notify_job path"
  - "Windows-only tests (spawn_detached, startup_registration) guarded with pytest.mark.skipif(sys.platform != 'win32') to run on this machine but not fail on Linux CI"

patterns-established:
  - "Typer sub-app pattern: daemon_app + app.add_typer -- reusable for future CLI groupings"
  - "winotify bat-file launch target pattern -- reusable for any notification click action on Windows"
  - "Sync scheduler job testing: plain function call with patch context managers (no asyncio.run needed)"
  - "Platform-guarded tests: skipif(sys.platform != 'win32') for Windows-specific code"

requirements-completed: [INT-01, INT-02, INT-03, INT-04, INT-05, INT-06]

# Metrics
duration: 20min
completed: 2026-03-16
---

# Phase 4 Plan 03: CLI Wiring and Test Conversion Summary

**Typer daemon sub-app (start/stop/status) and interrupt command wired into CLI; desktop-notifier replaced with winotify for working click callbacks; all 11 tests passing; human-verified on Windows 11**

## Performance

- **Duration:** ~20 min (including human verification and winotify fix)
- **Started:** 2026-03-16T03:10:00Z
- **Completed:** 2026-03-16T03:30:00Z
- **Tasks:** 3/3 complete (2 auto + 1 human-verify checkpoint approved)
- **Files modified:** 6

## Accomplishments
- Replaced daemon() stub in cli.py with a full daemon_app Typer sub-app exposing start/stop/status subcommands
- Added interrupt() command that calls run_session(max_cards=1) -- closes the notification -> terminal -> quiz loop
- Converted all 11 xfail stubs in test_daemon.py to real passing unit tests (INT-01 through INT-06)
- Added test_interrupt_command to test_cli.py confirming max_cards=1 call via CliRunner
- Discovered and fixed desktop-notifier click callback issue on Windows (replaced with winotify)
- Human verified: toast notification appears, click opens terminal with hms interrupt, daemon lifecycle works end-to-end
- Full suite: pytest tests/ -x -q exits 0 (85 tests, 0 failures, 0 xfail)

## Task Commits

Each task was committed atomically:

1. **Task 1: Wire CLI daemon sub-app and interrupt command** - `506732a` (feat)
2. **Task 2: Convert xfail stubs to passing unit tests** - `d692ed8` (test)
3. **Task 3: Human verification checkpoint** - approved; winotify fix in `9288bbf` (fix)

**Plan metadata:** `ccd2c5d` (docs: initial summary before checkpoint)

## Files Created/Modified
- `src/hms/cli.py` - Added daemon_app sub-app (start/stop/status) and interrupt command; removed daemon() stub
- `tests/test_daemon.py` - Full rewrite: 11 real passing tests with mocks for all INT-01..INT-06 behaviors
- `tests/test_cli.py` - Added test_interrupt_command verifying run_session called with max_cards=1
- `src/hms/daemon/notifier.py` - Replaced desktop-notifier with winotify; bat-file click target pattern
- `src/hms/daemon/runner.py` - BackgroundScheduler + threading.Event replaces AsyncIOScheduler + asyncio
- `src/hms/daemon/scheduler.py` - notify_job became sync (no longer async coroutine)
- `pyproject.toml` - winotify replaces desktop-notifier in dependencies

## Decisions Made
- **Replaced desktop-notifier with winotify:** desktop-notifier WinRT on_clicked callbacks silently fail for unpackaged Python apps on Windows. winotify uses a bat-file launch target that Windows can open reliably from toast actions.
- **Bat-file click target pattern:** _ensure_bat() writes interrupt.bat to HMS_HOME; notification launch= and button launch= both point to it. This sidesteps the limitation that WinRT toast actions cannot invoke arbitrary command lines.
- **Sync notify_job + BackgroundScheduler:** With winotify being synchronous, the asyncio event loop is unnecessary. The runner was simplified to use BackgroundScheduler with threading.Event for the stop signal.
- **Patching Card.select not Card class:** Avoids MagicMock field descriptor issues where Card.due <= datetime raises TypeError in tests.
- **Windows-only test guards:** spawn_detached and startup_registration tests use skipif(sys.platform != "win32") so they run locally but don't fail on Linux CI.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Wrong patch targets in async scheduler tests**
- **Found during:** Task 2 (xfail stub conversion)
- **Issue:** Initial patches for ensure_initialized, load_config, and Card used wrong module paths. Patching Card entirely caused MagicMock <= TypeError.
- **Fix:** Changed patches to hms.init.ensure_initialized, hms.config.load_config, and hms.models.Card.select respectively
- **Files modified:** tests/test_daemon.py
- **Verification:** All 11 tests pass after fix
- **Committed in:** d692ed8 (Task 2 commit)

**2. [Rule 1 - Bug] desktop-notifier click callbacks non-functional on Windows**
- **Found during:** Task 3 (human verification -- Step 6 notification click)
- **Issue:** desktop-notifier's WinRT on_clicked callback does not fire for unpackaged Python apps on Windows 11. This is a known limitation of WinRT for non-MSIX apps.
- **Fix:** Replaced desktop-notifier with winotify. Notification click uses bat-file launch target. notify_job became sync; runner simplified to BackgroundScheduler.
- **Files modified:** pyproject.toml, src/hms/daemon/notifier.py, src/hms/daemon/runner.py, src/hms/daemon/scheduler.py, tests/test_daemon.py
- **Verification:** Human verified -- toast appears, click opens terminal running hms interrupt, session completes
- **Committed in:** 9288bbf (fix commit)

---

**Total deviations:** 2 auto-fixed (both Rule 1 -- bugs discovered during testing and verification)
**Impact on plan:** The winotify fix was a necessary library swap to achieve working notification clicks on Windows. It simplified the architecture (sync instead of async) without changing the user-facing behavior.

## Issues Encountered
- Async scheduler tests required careful patch target selection due to lazy imports inside notify_job(). Resolved by patching at the module that owns the object, not where it's used.
- desktop-notifier's WinRT integration does not support click callbacks for unpackaged Python apps. This was the highest-risk item flagged in 04-RESEARCH.md (Pitfall 4). Resolved by switching to winotify with bat-file launch target.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 4 (Interrupt Daemon) is complete -- all 4 plans executed, all tests passing, human verified
- Phase 5 (AI Content Generation) can proceed -- requires only Phase 1 foundation (data model, YAML schema)
- No blockers remaining for Phase 4

---
*Phase: 04-interrupt-daemon*
*Completed: 2026-03-16*

## Self-Check: PASSED
