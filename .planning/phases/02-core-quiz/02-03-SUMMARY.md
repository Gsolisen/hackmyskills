---
phase: 02-core-quiz
plan: "03"
subsystem: quiz
tags: [rich, fsrs, readchar, scenario, explain-concept, tdd]

# Dependency graph
requires:
  - phase: 02-core-quiz/02-01
    provides: quiz.py skeleton with SessionResult, persist_rating, _wait_for_key, and handler stubs
  - phase: 02-core-quiz/02-02
    provides: _handle_flashcard and _handle_command_fill implementations + test infrastructure pattern
provides:
  - _handle_scenario: A/B/C/D keypress scenario question handler with immediate feedback and explanation
  - _handle_explain_concept: free-text + 1-4 self-rating explain-concept handler
  - test_scenario_flow: real passing tests for correct and wrong scenario selections
  - test_explain_concept_flow: real passing test for explain-concept with mock input and readkey
affects: [02-04-session-loop, 02-05-summary-display]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Handler signature: (card, q_data, session, _readkey=None) for all question types"
    - "Console suppression in tests: quiz_mod.console = Console(file=io.StringIO()) pattern"
    - "builtins.input monkeypatched via unittest.mock.patch for command-fill and explain-concept"
    - "mock_readkey as iterator-backed closure: keys=iter([...]); def mock_readkey(): return next(keys)"

key-files:
  created: []
  modified:
    - src/hms/quiz.py
    - tests/test_quiz.py

key-decisions:
  - "xfail stubs converted to real tests by replacing raise NotImplementedError with full test bodies"
  - "test_scenario_flow split into test_scenario_flow_correct and test_scenario_flow_wrong; alias preserves test_scenario_flow name"
  - "explain-concept uses input() (not _readkey) for free-text — monkeypatched via builtins.input in tests"

patterns-established:
  - "Scenario handler: blue Panel for situation, letter choices printed below, single keypress, color feedback, dim explanation panel, any-key-to-continue"
  - "Explain-concept handler: blue Panel for prompt, input() for reflection, green Panel for model answer, 1-4 rating keypress"

requirements-completed: [QUIZ-06, QUIZ-07]

# Metrics
duration: 3min
completed: 2026-03-15
---

# Phase 2 Plan 03: Scenario and Explain-Concept Handler Summary

**_handle_scenario (A/B/C/D keypress with immediate feedback) and _handle_explain_concept (free-text + 1-4 self-rating) implemented in quiz.py; both handler tests pass green with mock input injection**

## Performance

- **Duration:** ~3 min
- **Started:** 2026-03-15T21:34:59Z
- **Completed:** 2026-03-15T21:37:11Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- Implemented `_handle_scenario` with blue Panel for situation, A/B/C/D keypress, correct/incorrect Rich-colored feedback, explanation panel, any-key-to-continue, and `persist_rating` call
- Implemented `_handle_explain_concept` with blue Panel for prompt, `input()` for free-text reflection (unevaluated), green Panel for model answer, 1-4 self-rating keypress, and `persist_rating` call
- Removed xfail stubs and replaced with real tests: `test_scenario_flow_correct`, `test_scenario_flow_wrong`, and `test_explain_concept_flow` — all passing green

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement _handle_scenario and _handle_explain_concept** - `915a526` (feat)
2. **Task 2: Convert scenario and explain-concept xfail stubs to real tests** - `9a2fe2c` (test)

## Files Created/Modified
- `src/hms/quiz.py` - _handle_scenario and _handle_explain_concept stubs replaced with full implementations
- `tests/test_quiz.py` - xfail stubs replaced with real test functions; _handle_scenario/_handle_explain_concept added to imports

## Decisions Made
- test_scenario_flow split into two functions (correct/wrong) to independently verify both rating branches; `test_scenario_flow = test_scenario_flow_correct` alias preserves plan-referenced test name
- explain-concept uses `input()` (not `_readkey`) for free-text entry, following the plan spec — monkeypatched via `unittest.mock.patch("builtins.input", ...)` in tests

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - Plan 02 had already updated quiz.py to the `(card, q_data, session, _readkey=None)` signature and moved from stubs, so only the scenario and explain-concept stubs remained to implement.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All four question-type handlers are now implemented (flashcard, command-fill, scenario, explain-concept)
- Plan 04 can assemble the full session loop and wire run_session to use all handlers without any NotImplementedError stubs
- Plan 04 can also implement _show_summary (currently a stub) as the final session display

---
*Phase: 02-core-quiz*
*Completed: 2026-03-15*
