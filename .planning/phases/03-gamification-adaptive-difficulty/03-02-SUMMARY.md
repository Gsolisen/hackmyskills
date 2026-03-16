---
phase: 03-gamification-adaptive-difficulty
plan: 02
subsystem: quiz-engine
tags: [gamification, adaptive-difficulty, xp, streaks, unlocks, tdd]
dependency_graph:
  requires: [03-01]
  provides: [quiz-xp-integration, unlock-aware-queue, session-unlock-notifications]
  affects: [src/hms/quiz.py, tests/test_quiz.py]
tech_stack:
  added: []
  patterns: [per-card-xp-accumulation, unlock-gate-filtering, peewee-or-conditions]
key_files:
  created: []
  modified:
    - src/hms/quiz.py
    - tests/test_quiz.py
decisions:
  - "SessionResult.xp computes lazily at property call time using snapshot streak from compute_streak_with_freeze()"
  - "build_queue unlocked_tiers filter uses functools.reduce(operator.or_) for Peewee OR conditions"
  - "compute_streak() function kept in quiz.py (not deleted) but no longer called — replaced by compute_streak_with_freeze()"
  - "run_session uses unlocked_tiers only for no-topic sessions; topic-specific sessions bypass the filter"
metrics:
  duration: 3 min
  completed_date: "2026-03-15"
  tasks_completed: 2
  files_modified: 2
---

# Phase 3 Plan 02: Quiz-Gamification Integration Summary

Wire gamification module into quiz session engine: per-card XP formula replaces placeholder, build_queue filters locked tiers, run_session computes unlock diffs and shows notifications.

## Tasks Completed

| # | Task | Commit | Files |
|---|------|--------|-------|
| 1 | Per-card XP accumulation in SessionResult and tier-aware build_queue | 35e2061 | src/hms/quiz.py, tests/test_quiz.py |
| 2 | run_session unlock-awareness and session summary unlock notifications | 5583e9b | src/hms/quiz.py, tests/test_quiz.py |

## What Was Built

### SessionResult — Per-Card XP

- Added `cards_reviewed: list[tuple]` field (tier, rating_value pairs)
- Updated `record()` to accept `tier: str = "L1"` and append to `cards_reviewed`
- Replaced `xp` placeholder (`total * 15`) with sum of `compute_xp_for_review(tier, rating_value, streak)` calls
- `ratings` list kept for backward compatibility

### build_queue — Unlock-Aware Filtering

- Added `unlocked_tiers: Optional[dict]` parameter
- When provided, applies Peewee OR conditions (`functools.reduce(operator.or_, conditions)`) to filter cards by topic+tier
- All four handler `session.record()` calls updated to pass `tier=card.tier`

### run_session — Unlock Integration

- Snapshots `get_unlocked_tiers_per_topic()` before session loop
- Passes `unlocked_tiers` to `build_queue` for no-topic sessions
- After session loop: calls `award_freeze_if_due()` for streak milestone freezes
- Computes `new_unlocks` diff (before vs after) and passes to `_show_summary`

### _show_summary — Freeze-Aware Streak + Unlock Notifications

- Switched from `compute_streak()` to `compute_streak_with_freeze()`
- Shows freeze count in streak display when freeze_count > 0
- Accepts `new_unlocks: Optional[list]` parameter
- Prints unlock notification line per newly unlocked (topic, tier) pair

## Tests Added / Updated

| Test | File | Status |
|------|------|--------|
| test_session_result_accuracy | tests/test_quiz.py | Updated: xp==5 (was 30) |
| test_build_queue_respects_unlock | tests/test_quiz.py | New: L2 card excluded |
| test_build_queue_serves_unlocked_tiers | tests/test_quiz.py | New: L1+L2 both served |
| test_unlock_notification_shown | tests/test_quiz.py | New: unlock message in output |

Full suite: 70 tests, all passing.

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check: PASSED

- [x] src/hms/quiz.py exists and contains `from hms.gamification import`
- [x] src/hms/quiz.py does NOT contain `return self.total * 15`
- [x] src/hms/quiz.py contains `unlocked_tiers` in build_queue signature
- [x] src/hms/quiz.py contains `new_unlocks` in _show_summary and run_session
- [x] tests/test_quiz.py contains `test_build_queue_respects_unlock`
- [x] tests/test_quiz.py contains `test_unlock_notification_shown`
- [x] All commits exist: e990788, 35e2061, 5583e9b
- [x] python -m pytest tests/ -x -q exits 0
