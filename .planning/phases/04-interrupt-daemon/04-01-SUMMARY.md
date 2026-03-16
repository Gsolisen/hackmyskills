---
phase: 04-interrupt-daemon
plan: "01"
subsystem: daemon
tags: [windows, psutil, winreg, subprocess, platform-abstraction, config]

# Dependency graph
requires:
  - phase: 04-00
    provides: DaemonPlatform ABC and daemon package skeleton

provides:
  - WindowsPlatform with winreg startup registration and DETACHED_PROCESS spawn
  - LinuxPlatform and MacOSPlatform stubs (NotImplementedError)
  - run_session max_cards parameter for interrupt mini-session cap
  - DEFAULT_CONFIG daemon sub-dict with interval_minutes, work_hours, daily_cap

affects:
  - 04-02 (daemon scheduler imports WindowsPlatform via get_platform())
  - 04-03 (interrupt CLI calls run_session with max_cards)

# Tech tracking
tech-stack:
  added: [psutil (is_running), winreg (registry, lazy imported)]
  patterns: [lazy platform import in WindowsPlatform methods, lazy psutil import handled via try/except NoSuchProcess]

key-files:
  created:
    - src/hms/daemon/platform/windows.py
    - src/hms/daemon/platform/linux.py
    - src/hms/daemon/platform/macos.py
  modified:
    - src/hms/quiz.py
    - src/hms/config.py

key-decisions:
  - "winreg imported lazily inside register_startup/unregister_startup to avoid ImportError on non-Windows"
  - "interval_minutes kept at top level of DEFAULT_CONFIG for backward compatibility with existing config readers"
  - "daemon.daily_cap=10 (not 25) — interrupt sessions are intentionally shorter than full daily sessions"

patterns-established:
  - "Platform stub pattern: all 4 abstract methods raise NotImplementedError with 'not implemented in v1' message"
  - "spawn_detached uses DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | DEVNULL for all streams — no console window"
  - "unregister_startup catches FileNotFoundError silently — idempotent by design"

requirements-completed: [INT-01, INT-02, INT-05, INT-06]

# Metrics
duration: 2min
completed: 2026-03-16
---

# Phase 4 Plan 01: Platform Layer + Cross-Cutting Changes Summary

**WindowsPlatform (winreg startup + DETACHED_PROCESS spawn) with Linux/macOS stubs, plus max_cards cap on run_session and daemon config defaults**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-16T02:59:58Z
- **Completed:** 2026-03-16T03:01:58Z
- **Tasks:** 2
- **Files modified:** 5

## Accomplishments

- WindowsPlatform implemented with all 4 concrete methods: winreg register/unregister startup, DETACHED_PROCESS spawn returning child PID, psutil is_running with NoSuchProcess guard
- LinuxPlatform and MacOSPlatform stubs created — all 4 methods raise NotImplementedError
- run_session() accepts max_cards: Optional[int] = None; applies min(daily_cap, max_cards) when set
- DEFAULT_CONFIG extended with daemon sub-dict: interval_minutes=90, work_hours_start="09:00", work_hours_end="21:00", daily_cap=10

## Task Commits

1. **Task 1: Implement platform layer (WindowsPlatform + stubs)** - `35d478f` (feat)
2. **Task 2: Add max_cards to run_session() and [daemon] defaults to load_config()** - `db772e0` (feat)

## Files Created/Modified

- `src/hms/daemon/platform/windows.py` - WindowsPlatform with 4 concrete methods (winreg + DETACHED_PROCESS spawn + psutil)
- `src/hms/daemon/platform/linux.py` - LinuxPlatform stub raising NotImplementedError for all 4 methods
- `src/hms/daemon/platform/macos.py` - MacOSPlatform stub raising NotImplementedError for all 4 methods
- `src/hms/quiz.py` - run_session() signature extended with max_cards parameter + min() enforcement
- `src/hms/config.py` - DEFAULT_CONFIG extended with [daemon] sub-dict

## Decisions Made

- winreg imported lazily inside WindowsPlatform methods to avoid ImportError on Linux/macOS where winreg does not exist
- interval_minutes kept at DEFAULT_CONFIG top level for backward compatibility — existing code reading `config["interval_minutes"]` continues to work without changes
- daemon.daily_cap=10 mirrors the research spec — interrupt sessions are intentionally capped lower than the full 25-card daily sessions

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Platform layer complete; `get_platform()` in `__init__.py` already routes to WindowsPlatform on win32
- run_session max_cards ready for interrupt CLI (04-03) to pass session length
- daemon config defaults prevent KeyError in 04-02 scheduler when reading `cfg["daemon"]["interval_minutes"]`

---
*Phase: 04-interrupt-daemon*
*Completed: 2026-03-16*
