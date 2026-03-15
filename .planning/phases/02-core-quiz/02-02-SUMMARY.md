---
phase: 02-core-quiz
plan: 02
subsystem: quiz
tags: [rich, fsrs, peewee, pytest, tdd]

# Dependency graph
requires:
  - phase: 02-01
    provides: quiz.py scaffold with NotImplementedError stubs, _wait_for_key, persist_rating, SessionResult, run_session
  - phase: 01-03
    provides: load_questions() YAML loader, Card model

provides:
  - _handle_flashcard: displays blue Panel, flips on any key, green Panel for answer, 1-4 rating -> Again/Hard/Good/Easy
  - _handle_command_fill: displays blue Panel, accepts typed input, case-insensitive exact match, Good/Again rating
  - Both handlers call persist_rating() and session.record() with correct arguments
  - Handler signatures updated to (card, q_data, session, _readkey=None)
  - run_session loads all questions once via load_questions() and passes q_data per card

affects: [02-03, 02-04]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "q_data dict passed to handlers from a pre-built questions_by_id lookup in run_session"
    - "Handler signature: (card, q_data, session, _readkey=None) for all question types"
    - "Test output suppression: replace quiz_mod.console with Console(file=io.StringIO())"
    - "Mock _readkey: iterator-based generator for deterministic keypress sequences"

key-files:
  created: []
  modified:
    - src/hms/quiz.py
    - tests/test_quiz.py

key-decisions:
  - "q_data loaded once at run_session() start (questions_by_id dict), not per card — avoids repeated YAML reads"
  - "Handler signatures shifted to (card, q_data, session, _readkey=None) — q_data is second positional arg"
  - "_handle_command_fill uses case-insensitive exact match only (no fuzzy matching)"
  - "Flashcard rating Good(3) and Easy(4) both count as correct in session.record()"

patterns-established:
  - "All handlers accept (card, q_data, session, _readkey=None) — consistent injectable test interface"
  - "Console output suppressed in tests by replacing quiz_mod.console module-level attribute"

requirements-completed: [QUIZ-04, QUIZ-05]

# Metrics
duration: 2min
completed: 2026-03-15
---

# Phase 2 Plan 02: Flashcard and Command-Fill Handlers Summary

**_handle_flashcard with blue/green Rich Panels and 1-4 FSRS ratings, _handle_command_fill with case-insensitive exact match and Good/Again rating, both persisting FSRS state via persist_rating()**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-15T20:54:38Z
- **Completed:** 2026-03-15T20:56:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments

- _handle_flashcard implemented: clears screen, shows question in blue Panel, waits for flip keypress, shows answer in green Panel, collects 1-4 rating, calls persist_rating and session.record
- _handle_command_fill implemented: shows prompt in blue Panel, accepts typed command, case-insensitive exact match, shows result, calls persist_rating (Good/Again) and session.record
- All three handler tests converted from xfail stubs to real passing assertions (test_flashcard_flow, test_command_fill_correct, test_command_fill_incorrect)
- run_session updated to load all questions once and pass q_data to each handler

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement _handle_flashcard and _handle_command_fill** - `b34595e` (feat)
2. **Task 2: Convert flashcard and command-fill xfail tests to real assertions** - `6f555f0` (feat)

**Plan metadata:** (docs: complete plan — see final commit)

## Files Created/Modified

- `src/hms/quiz.py` - Implemented both handlers, updated handler signatures to (card, q_data, session, _readkey=None), updated run_session to build questions_by_id lookup, added load_questions import
- `tests/test_quiz.py` - Replaced three xfail stubs with real assertions using mock _readkey and patched builtins.input

## Decisions Made

- q_data passed to handlers from a pre-built lookup dict in run_session — avoids per-card YAML re-reads as specified in the plan
- Handler signature shifted to (card, q_data, session, _readkey=None) — q_data is second positional arg, consistent across all four handler types
- _handle_command_fill uses case-insensitive exact match only — no fuzzy matching (explicitly specified in plan)
- Test console suppression done by replacing quiz_mod.console module-level attribute with Console(file=io.StringIO())

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Both flashcard and command-fill handlers are working and tested
- Handler signature contract (card, q_data, session, _readkey=None) established for scenario and explain-concept handlers (Plan 03)
- run_session question lookup pattern ready for Plan 04 session loop
- All 9 non-xfail quiz tests pass; 2 remaining xfail stubs (scenario, explain-concept) are expected

---
*Phase: 02-core-quiz*
*Completed: 2026-03-15*
