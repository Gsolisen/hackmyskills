---
phase: 01-foundation
plan: "02"
subsystem: database
tags: [python, peewee, sqlite, fsrs, tdd, deferred-init, wal]

# Dependency graph
requires:
  - phase: 01-01
    provides: "Installable package, hms.config.HMS_HOME, conftest hms_home fixture, xfail test stubs"
provides:
  - Deferred SqliteDatabase object and BaseModel (hms.db)
  - Card and ReviewHistory Peewee models (hms.models)
  - Thin FSRS wrapper — review_card() function (hms.scheduler)
  - ensure_initialized() first-run setup with idempotent db.init + create_tables (hms.init)
  - data.db created in HMS_HOME on first run
  - config.toml written on first run with commented defaults
  - Full test coverage for FOUND-02, FOUND-06, FOUND-07 (12 tests green)
affects: [01-03, all-subsequent-phases]

# Tech tracking
tech-stack:
  added:
    - peewee>=4.0.1 (ORM, already installed in 01-01 — now actively used)
    - fsrs>=6.3.1 (FSRS-6 scheduler — Scheduler, Card, Rating, ReviewLog)
  patterns:
    - Deferred SqliteDatabase(None) — db.init() called in ensure_initialized(), not at import
    - safe=True on db.create_tables() for idempotent re-runs
    - WAL + foreign_keys pragmas on db.init()
    - fsrs state stored as JSON blob in Card.fsrs_state + indexed due DateTimeField for queries
    - UTC-aware due from fsrs stripped to naive via .replace(tzinfo=None) before SQLite storage
    - hms.config.HMS_HOME imported in init.py (not re-declared) so monkeypatching propagates
    - conftest hms_home fixture: db.init() in setup, db.close() in teardown

key-files:
  created:
    - src/hms/db.py
    - src/hms/models.py
    - src/hms/init.py
    - src/hms/scheduler.py
  modified:
    - tests/conftest.py
    - tests/test_init.py
    - tests/test_models.py
    - tests/test_scheduler.py
    - src/hms/cli.py

key-decisions:
  - "FSRS Card has no reps/lapses attributes in v6 — Card model tracks them as manually-incremented IntegerField(default=0) for future stats"
  - "UTC-aware due datetime from fsrs stripped to naive via .replace(tzinfo=None) before Peewee DateTimeField storage — avoids Pitfall 3 TypeError"
  - "re-read hms.config.HMS_HOME at ensure_initialized() call time (import hms.config as _cfg; _cfg.HMS_HOME) to respect monkeypatching in test isolation"

patterns-established:
  - "Deferred init: db = SqliteDatabase(None) + initialize_db(path) called in ensure_initialized()"
  - "Test isolation: hms_home fixture in conftest.py does db.init(tmp_path/test.db) + db.create_tables() + yield + db.close()"
  - "FSRS round-trip: FsrsCard() -> review_card() -> updated_card.to_json() stored in Card.fsrs_state; due stored naive UTC"

requirements-completed:
  - FOUND-02
  - FOUND-06
  - FOUND-07

# Metrics
duration: 3min
completed: 2026-03-13
---

# Phase 01 Plan 02: Data Model, FSRS Scheduler, and First-Run Init Summary

**Peewee deferred-init SQLite schema (Card + ReviewHistory), FSRS v6 review_card() wrapper, and idempotent ensure_initialized() — 12 tests green including all FOUND-02/06/07 assertions**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-13T21:16:42Z
- **Completed:** 2026-03-13T21:19:03Z
- **Tasks:** 2
- **Files modified:** 9

## Accomplishments

- `data.db` created in `~/.hackmyskills/` on first run via `ensure_initialized()` with WAL mode and foreign key enforcement
- Card and ReviewHistory Peewee models with full FSRS state fields; schema creation is idempotent (safe=True)
- `fsrs.Scheduler.review_card()` wrapped in `hms.scheduler.review_card()` — all four ratings return UTC-aware `due` datetime
- `config.toml` written on first run with commented defaults (daily_cap, interval_minutes, quiet_hours)
- All xfail stubs for FOUND-02, FOUND-06, FOUND-07 converted to real green assertions; 12 tests pass, 3 xfail (loader, expected for Plan 01-03)

## Task Commits

Each task was committed atomically:

1. **Task 1: Peewee db object, Card/ReviewHistory models, deferred init** - `c5e80a4` (feat)
2. **Task 2: FSRS scheduler wrapper and full test coverage** - `cb132d6` (feat)

## Files Created/Modified

- `src/hms/db.py` - Deferred SqliteDatabase(None), BaseModel, initialize_db()
- `src/hms/models.py` - Card and ReviewHistory Peewee models; no create_tables at import
- `src/hms/init.py` - ensure_initialized() with mkdir, db.init, create_tables, content stub, config write
- `src/hms/scheduler.py` - Thin wrapper: scheduler = Scheduler(); review_card(card, rating) -> (Card, ReviewLog)
- `tests/conftest.py` - Extended hms_home fixture: db.init() + create_tables() + db.close()
- `tests/test_init.py` - 4 real tests (xfail removed): db creation, content dir, config.toml, idempotency
- `tests/test_models.py` - 2 real tests: FSRS state roundtrip, review history persistence with rating assertion
- `tests/test_scheduler.py` - 3 real tests: due updated, all ratings accepted, log has rating
- `src/hms/cli.py` - _show_dashboard() calls ensure_initialized() and shows real HMS_HOME path

## Decisions Made

- **FSRS Card has no `reps`/`lapses` in v6:** `fsrs.Card` dataclass fields are `card_id`, `state`, `step`, `stability`, `difficulty`, `due`, `last_review`. The Peewee Card model tracks `reps` and `lapses` as manually-incremented `IntegerField(default=0)` for future stats/adaptive difficulty — zero cost, not from FSRS.
- **UTC naive storage:** `updated_card.due.replace(tzinfo=None)` before writing to `DateTimeField` avoids the Pitfall 3 `TypeError: can't compare offset-naive and offset-aware datetimes` at query time. Comparisons use `datetime.now(timezone.utc)` where needed.
- **Re-read HMS_HOME at call time:** `ensure_initialized()` does `import hms.config as _cfg; home = _cfg.HMS_HOME` instead of using the module-level `HMS_HOME` constant, so `monkeypatch.setattr("hms.config.HMS_HOME", ...)` in tests is respected without re-importing.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Re-read HMS_HOME at call time in ensure_initialized()**
- **Found during:** Task 1 (test_first_run_creates_db)
- **Issue:** `from hms.config import HMS_HOME` binds `HMS_HOME` at import time. Monkeypatching `hms.config.HMS_HOME` in tests would not affect the already-bound name inside `init.py`, causing tests to write to the real `~/.hackmyskills/`.
- **Fix:** Changed `ensure_initialized()` to do `import hms.config as _cfg; home = _cfg.HMS_HOME` at call time so the monkeypatched attribute is read dynamically.
- **Files modified:** `src/hms/init.py`
- **Verification:** `test_first_run_creates_db` creates `data.db` inside `tmp_path`, not `~/.hackmyskills/`
- **Committed in:** `c5e80a4` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 bug)
**Impact on plan:** Essential fix for test isolation — without it all init tests would pollute the real home directory.

## Issues Encountered

None beyond the one auto-fixed deviation above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Data core complete: `Card`, `ReviewHistory`, `ensure_initialized()`, `review_card()` all working
- Plan 01-03 can proceed: add real YAML content files to `src/hms/content/`, implement `hms/loader.py`, flip test_loader.py xfail stubs to real assertions
- Phase 2+ can import `hms.db.db`, `hms.models.Card`, `hms.models.ReviewHistory`, `hms.scheduler.review_card` without modification

---
*Phase: 01-foundation*
*Completed: 2026-03-13*
