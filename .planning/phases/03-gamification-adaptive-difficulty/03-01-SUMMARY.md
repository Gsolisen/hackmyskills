---
phase: 03-gamification-adaptive-difficulty
plan: 01
subsystem: gamification
tags: [xp, streak, freeze, level, mastery, unlock, tdd]
dependency_graph:
  requires: []
  provides: [gamification_module, userstat_model]
  affects: [03-02, 03-03]
tech_stack:
  added: []
  patterns: [peewee-single-row-table, utc-date-streak-walk, tdd-red-green]
key_files:
  created:
    - src/hms/gamification.py
    - tests/test_gamification.py
  modified:
    - src/hms/models.py
    - src/hms/init.py
    - tests/conftest.py
decisions:
  - "Use datetime.utcnow().date() for streak walk to match UTC-stored review timestamps (avoids local/UTC date mismatch)"
  - "UserStat is a single-row table (id=1 always) for persistent freeze/streak state"
  - "mastery_ratio returns 1.0 (unlocked) when prereq tier has 0 cards — avoids ZeroDivisionError and sensible default"
metrics:
  duration: "3 min"
  completed_date: "2026-03-15"
  tasks_completed: 4
  files_changed: 5
---

# Phase 3 Plan 01: Gamification Module Summary

TDD implementation of the complete gamification computational core: XP formula, streak+freeze logic, level derivation, mastery queries, and tier unlock checks. All downstream Phase 3 plans (03-02, 03-03) import from this module.

## What Was Built

- `src/hms/gamification.py` — Full gamification module with 10 exported symbols (XP, streak, freeze, levels, mastery, unlock, display)
- `tests/test_gamification.py` — 29 unit tests covering all specified behaviors (all green)
- `src/hms/models.py` — Added `UserStat` model (single-row persistent gamification state)
- `src/hms/init.py` — Updated `db.create_tables` to include `UserStat`
- `tests/conftest.py` — Updated `db.create_tables` fixture to include `UserStat`

## TDD Flow

| Step | Commit | Status |
|------|--------|--------|
| RED — model + conftest updates + failing tests | ca690c1 | All 29 tests failed (ImportError) |
| GREEN — implement gamification.py + bug fix | ca13fd9 | All 29 passed; full suite 67/67 |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] UTC vs local date mismatch in streak walk**
- **Found during:** GREEN phase, first test run (test_streak_consecutive failed: assert 2 == 3)
- **Issue:** `compute_streak_with_freeze()` used `date.today()` (local timezone) while `ReviewHistory.reviewed_at` stores naive UTC datetimes. On a machine where local time is behind UTC, the review stored for "today" via `datetime.utcnow()` had a UTC date one day ahead of `date.today()`, causing the streak walk to miss the most recent review.
- **Fix:** Changed `current = date.today()` to `current = datetime.utcnow().date()` in the streak walk, ensuring both the stored dates and the walk date are in UTC.
- **Files modified:** `src/hms/gamification.py`
- **Commit:** ca13fd9

## Self-Check: PASSED

Files verified:
- FOUND: src/hms/gamification.py
- FOUND: tests/test_gamification.py
- FOUND: src/hms/models.py (class UserStat present)
- FOUND: src/hms/init.py (UserStat in db.create_tables)
- FOUND: tests/conftest.py (UserStat in db.create_tables)

Commits verified:
- FOUND: ca690c1 (RED — test commit)
- FOUND: ca13fd9 (GREEN — implementation commit)

Test results: 67/67 passed (full suite)
