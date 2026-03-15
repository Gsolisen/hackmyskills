---
phase: 02-core-quiz
plan: 04
subsystem: quiz
tags: [rich, fsrs, peewee, session-summary, tdd]

# Dependency graph
requires:
  - phase: 02-core-quiz/02-01
    provides: SessionResult, build_queue, run_session skeleton, _HANDLER_DISPATCH
  - phase: 02-core-quiz/02-02
    provides: _handle_flashcard, _handle_command_fill implementations
  - phase: 02-core-quiz/02-03
    provides: _handle_scenario, _handle_explain_concept implementations
provides:
  - _show_summary() with full Panel (cards, accuracy, XP bold yellow, streak, due-tomorrow)
  - Mini-summary via is_partial=True (no due-tomorrow, no per-topic table)
  - Per-topic Rich Table for multi-topic full sessions only
  - Fully functional run_session() loop with all four handler dispatches
  - topic existence check in run_session() with red Panel (no ValueError)
  - hms quiz end-to-end functional (pending human-verify checkpoint)
affects:
  - 03-stats
  - 04-interrupt-daemon

# Tech tracking
tech-stack:
  added: [rich.table.Table]
  patterns:
    - _show_summary returns early for zero-card sessions (no output)
    - Topic existence check in run_session() shows red Panel, not ValueError exception
    - Missing question data skipped with dim warning (no exception)
    - KeyboardInterrupt shows mini-summary then returns cleanly

key-files:
  created: []
  modified:
    - src/hms/quiz.py
    - tests/test_quiz.py

key-decisions:
  - "Topic existence check moved from build_queue (ValueError) to run_session (red Panel display) — avoids exception-as-control-flow for a non-exceptional user action"
  - "Per-topic breakdown table shown only for multi-topic full sessions (not partial/mini-summary)"
  - "Zero-card _show_summary returns immediately — no summary Panel for empty sessions"

patterns-established:
  - "Summary panels use border_style=cyan, title bold, XP in bold yellow markup"
  - "Mini-summary (is_partial=True) omits due-tomorrow count and per-topic table"

requirements-completed: [QUIZ-08]

# Metrics
duration: 3min
completed: 2026-03-15
---

# Phase 2 Plan 04: Session Summary and run_session Completion Summary

**_show_summary() with Rich Panel (cards, accuracy, XP bold yellow, streak, due-tomorrow) and per-topic breakdown table; run_session() fully wired with all four handler dispatches, graceful Ctrl-C, and topic existence error Panel**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-15T20:59:59Z
- **Completed:** 2026-03-15T21:02:58Z
- **Tasks:** 2/3 (Task 3 is human-verify checkpoint)
- **Files modified:** 2

## Accomplishments
- _show_summary(): full Panel with cards reviewed, accuracy %, XP in bold yellow, streak with fire emoji, due-tomorrow count; mini-summary skips due-tomorrow/per-topic table
- Per-topic Rich Table rendered only for multi-topic full sessions (len > 1 and not partial)
- run_session() replaced ValueError pattern with topic existence check showing a red Panel
- Cards with missing question data skipped with dim warning (no exception raised)
- 5 new/updated tests; full suite 38/38 green

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement _show_summary and complete run_session loop** - `5463725` (feat)
2. **Task 2: Add session summary test and verify full suite green** - `23e0e92` (feat)
3. **Task 3: Verify end-to-end quiz session in real terminal** - awaiting human verify

## Files Created/Modified
- `src/hms/quiz.py` - _show_summary() implemented; build_queue() ValueError removed; run_session() topic existence check via red Panel; missing q_data skip with dim warning
- `tests/test_quiz.py` - test_show_summary_single_topic, test_show_summary_multi_topic, test_show_summary_empty added; test_no_cards_for_topic updated; test_run_session_unknown_topic added

## Decisions Made
- Topic existence check moved from build_queue (ValueError) to run_session (red Panel) — avoids exception-as-control-flow for a non-exceptional user action
- Per-topic breakdown table shown only for multi-topic full sessions, not for partial/mini-summaries
- Zero-card _show_summary returns immediately with no output

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- hms quiz end-to-end functional — pending human verification of terminal rendering (Task 3 checkpoint)
- All four question types dispatched correctly; session summary renders; Ctrl-C mini-summary works
- Phase 3 (Stats) can begin after human verify approval

---
*Phase: 02-core-quiz*
*Completed: 2026-03-15*
