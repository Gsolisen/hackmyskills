---
phase: 03-gamification-adaptive-difficulty
plan: 03
subsystem: ui
tags: [rich, typer, gamification, cli, dashboard, stats]

# Dependency graph
requires:
  - phase: 03-gamification-adaptive-difficulty/03-01
    provides: gamification module with XP, streak, freeze, levels, mastery/unlock functions
  - phase: 03-gamification-adaptive-difficulty/03-02
    provides: quiz integration that accumulates XP and surfaces unlock notifications

provides:
  - "`hms stats` command: Rich Panel with streak, level name, XP progress bar, cards due today, and per-topic breakdown table"
  - "Updated `hms` dashboard (no-args) with motivating streak+level+due headline, or welcome message on first run"
  - "Both commands handle empty DB gracefully (no crash on first run)"

affects: [04-interrupt-daemon, future-reporting, onboarding]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Lazy imports inside functions to avoid circular imports (gamification functions imported inside stats/dashboard methods)"
    - "_render_stats_panel() extracted from stats() for testability"
    - "ensure_initialized() called at top of each command before any DB access"

key-files:
  created: []
  modified:
    - src/hms/cli.py
    - tests/test_cli.py

key-decisions:
  - "_render_stats_panel() extracted as a separate private function from stats() — allows direct testing without CLI runner overhead and mirrors the existing quiz.py pattern"
  - "Per-topic mastery% computed directly from Card.state == 'Review' count vs total — avoids calling mastery_ratio() per card which would cause N+1 queries in wide topic sets"
  - "Dashboard shows emoji fire character inline in headline string — accepted as the simplest motivating visual without adding a Rich markup dependency"

patterns-established:
  - "Stats panel pattern: lazy-import gamification module inside render function, build summary string, build Rich Table, print Panel then Table separately"
  - "Dashboard pattern: check streak==0 and total_xp==0 as 'first-run' signal for welcome message branch"

requirements-completed: [GAME-04, GAME-05, ADAPT-01, ADAPT-03, ADAPT-04]

# Metrics
duration: 15min
completed: 2026-03-15
---

# Phase 3 Plan 03: Stats Command and Dashboard Update Summary

**`hms stats` Rich Panel with streak/level/XP-bar/per-topic table, and updated dashboard showing motivating streak+level+due headline replacing Phase 1 static placeholder**

## Performance

- **Duration:** ~15 min
- **Started:** 2026-03-15T22:00:00Z
- **Completed:** 2026-03-16T01:30:00Z
- **Tasks:** 2 (1 auto, 1 human-verify checkpoint)
- **Files modified:** 2

## Accomplishments
- `hms stats` replaces the "Not yet implemented" stub with a full Rich Panel: streak count, freeze indicator, level number and name, XP progress bar with block characters, cards due today, and a per-topic table showing Topic / Due / Mastery% / highest unlocked Tier
- `hms` (no-args dashboard) replaces the static Phase 1 placeholder ("Data home: ...") with a motivating one-liner (streak / level / due) or a welcome message on first run when no reviews exist
- All three automated tests (`test_stats_empty`, `test_stats_with_data`, `test_dashboard_updated`) pass; full test suite passes
- Human visual verification approved — Rich block-character XP bar, panel borders, and per-topic table confirmed correct in terminal

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement stats() command and update _show_dashboard()** - `c048b67` (feat)
   - RED test commit: `c9dc857` (test)
2. **Task 2: Visual verification of hms stats and hms dashboard** - human-approved checkpoint (no code commit)

## Files Created/Modified
- `src/hms/cli.py` - Added `_render_stats_panel()`, replaced `stats()` stub, updated `_show_dashboard()` with gamification data
- `tests/test_cli.py` - Added `test_stats_empty`, `test_stats_with_data`, `test_dashboard_updated`

## Decisions Made
- `_render_stats_panel()` extracted from `stats()` for testability — mirrors existing quiz.py pattern.
- Per-topic mastery% computed via `Card.state == 'Review'` count vs total to avoid N+1 queries from calling `mastery_ratio()` per card.
- Dashboard "first-run" condition is `streak == 0 and total_xp == 0` — simple, no false positives for users who reviewed then reset.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 3 gamification surface is complete: XP accumulation (03-01), quiz integration (03-02), and stats/dashboard display (03-03) all shipped.
- Phase 4 (Interrupt Daemon) can proceed; it will consume `hms stats` output indirectly via the daemon notification payload.
- Remaining concern: Windows WinRT notification permission flow is untested — needs validation before Phase 4 implementation begins.

---
*Phase: 03-gamification-adaptive-difficulty*
*Completed: 2026-03-15*
