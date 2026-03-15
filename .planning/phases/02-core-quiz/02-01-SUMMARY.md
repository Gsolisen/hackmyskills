---
phase: 02-core-quiz
plan: "01"
subsystem: quiz
tags: [readchar, fsrs, peewee, rich, typer, spaced-repetition]

# Dependency graph
requires:
  - phase: 01-foundation
    provides: Card/ReviewHistory models, FSRS scheduler, ensure_initialized(), load_config()
provides:
  - SessionResult dataclass with record(), accuracy_pct, xp
  - build_queue() with due-before-new ordering, daily_cap, and topic filter
  - persist_rating() atomic card update + ReviewHistory creation
  - compute_streak() consecutive-day calculation
  - run_session() stub dispatching to Wave 2 handlers
  - cli.py quiz() command with --topic/-t option
  - tests/test_quiz.py with xfail stubs for all Wave 2/3 behaviors
affects: [02-02, 02-03, 02-04, 03-stats-streaks]

# Tech tracking
tech-stack:
  added: [readchar>=4.0]
  patterns:
    - "Handler dispatch dict maps question_type strings to NotImplementedError stubs for Wave 2"
    - "db.atomic() context manager wraps Card save + ReviewHistory.create() for partial-session safety"
    - "Lazy readchar import in _wait_for_key avoids ImportError in test environments"
    - "xfail(strict=False) pattern for Wave 2 handler tests — they become green once handlers land"

key-files:
  created:
    - src/hms/quiz.py
    - tests/test_quiz.py
  modified:
    - src/hms/cli.py
    - pyproject.toml

key-decisions:
  - "readchar imported lazily inside _wait_for_key (not at module top) to avoid ImportError in test environments that lack a TTY"
  - "Handler stubs raise NotImplementedError(question_type) so Wave 2 plans fail fast on unimplemented types rather than silently skipping cards"
  - "quiz.py uses its own Console() instance, not imported from cli.py, to prevent circular imports"
  - "run_session() replaces module-level console for test capture via direct attribute assignment (quiz_mod.console = test_console)"

patterns-established:
  - "Atomic DB writes: use db.atomic() context for any multi-row write to prevent partial state on Ctrl-C"
  - "Topic validation: check count before queue build; raise ValueError with message for caller to display"

requirements-completed: [QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-09]

# Metrics
duration: 2min
completed: 2026-03-15
---

# Phase 2 Plan 01: Quiz Session Engine Skeleton Summary

**Quiz session skeleton with SessionResult, build_queue (due-before-new with daily_cap and topic filter), atomic persist_rating, compute_streak, run_session stub, and xfail test suite wiring cli.py --topic option**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T20:50:24Z
- **Completed:** 2026-03-15T20:52:24Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- Created `quiz.py` with full shared infrastructure used by all Wave 2 plans: SessionResult, build_queue, persist_rating, compute_streak, run_session
- Added `readchar>=4.0` dependency and wired `cli.py` quiz command with `--topic/-t` option
- Created `tests/test_quiz.py` with 6 passing tests and 5 xfail stubs covering all Wave 2/3 behaviors

## Task Commits

Each task was committed atomically:

1. **Task 1: Add readchar dependency and create quiz.py skeleton** - `55a6cf5` (feat)
2. **Task 2: Update cli.py quiz command and write xfail test stubs** - `9fe8c15` (feat)

**Plan metadata:** TBD (docs: complete plan)

## Files Created/Modified
- `src/hms/quiz.py` - Session engine: SessionResult, build_queue, persist_rating, compute_streak, run_session, handler stubs
- `tests/test_quiz.py` - 6 non-xfail tests + 5 xfail stubs for Wave 2 handlers
- `src/hms/cli.py` - quiz() command updated with --topic/-t option, delegates to quiz_module.run_session()
- `pyproject.toml` - Added readchar>=4.0 to project.dependencies

## Decisions Made
- readchar imported lazily inside `_wait_for_key` (not at module top-level) to avoid ImportError in test environments lacking a TTY
- Handler stubs raise `NotImplementedError(question_type)` so Wave 2 plans fail fast on unimplemented types
- `quiz.py` has its own `Console()` instance instead of importing from `cli.py` to prevent circular imports
- Test capture of Rich output done via replacing `quiz_mod.console` directly in the test, which keeps the production code clean

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## Next Phase Readiness
- `quiz.py` is fully importable by 02-02, 02-03, 02-04 without import errors
- All test stubs exist so Wave 2 plans can change xfail to passing tests as handlers are implemented
- `hms quiz --topic <topic>` wired and ready; Wave 2 handlers will populate the session loop

---
*Phase: 02-core-quiz*
*Completed: 2026-03-15*
