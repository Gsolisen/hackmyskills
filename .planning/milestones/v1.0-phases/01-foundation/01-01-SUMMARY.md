---
phase: 01-foundation
plan: "01"
subsystem: cli
tags: [python, typer, rich, hatchling, pytest, tomllib, pyproject]

# Dependency graph
requires: []
provides:
  - Installable Python package (pip install -e . works)
  - hms CLI entry point via hms.cli:app
  - Status dashboard on hms (no-args) showing Rich panel
  - hms --help, --version, subcommand stubs (quiz, stats, generate, daemon)
  - tomllib-based config reader with defaults in hms.config
  - pytest scaffold: conftest + 6 Wave 0 test files (3 real tests, 9 stubs)
affects: [01-02, 01-03, all-subsequent-phases]

# Tech tracking
tech-stack:
  added:
    - typer>=0.12.0 (CLI framework with CliRunner for tests)
    - rich>=13.0 (terminal output, Rich panels)
    - peewee>=4.0.1 (ORM, installed now, used in 01-02)
    - fsrs>=6.3.1 (FSRS-6 scheduler, installed now, used in 01-02)
    - pyyaml>=6.0 (YAML loading, installed now, used in 01-03)
    - pytest>=8.0 (test framework via dev extra)
  patterns:
    - src/hms/ layout with Hatchling build backend
    - hms.cli:app Typer entry point with invoke_without_command=True callback
    - Module-level HMS_HOME and CONFIG_PATH constants (monkeypatchable for test isolation)
    - tomllib.load() for reading config.toml (stdlib, no extra dependency)
    - xfail stubs for modules not yet created

key-files:
  created:
    - pyproject.toml
    - src/hms/__init__.py
    - src/hms/cli.py
    - src/hms/config.py
    - src/hms/content/__init__.py
    - tests/conftest.py
    - tests/test_cli.py
    - tests/test_init.py
    - tests/test_loader.py
    - tests/test_scheduler.py
    - tests/test_models.py
  modified: []

key-decisions:
  - "requires-python set to >=3.11 (not >=3.12 per plan) — Python 3.11 is installed and has tomllib; all target APIs available"
  - "src/hms/content/__init__.py added to satisfy importlib.resources.files() namespace package requirement"
  - "force-include for content dir retained in pyproject.toml even though no YAML files yet — avoids Hatchling FileNotFoundError on empty dir"
  - "Version flag implemented on the app callback (not a separate command) for clean --version behavior"

patterns-established:
  - "src/hms/ layout: all source code under src/hms/, Hatchling packages directive points there"
  - "CLI entry point pattern: @app.callback(invoke_without_command=True) for no-args dashboard"
  - "Test isolation: monkeypatch hms.config.HMS_HOME and hms.config.CONFIG_PATH to tmp_path"
  - "xfail stub pattern: mark tests for future modules with descriptive reason strings"

requirements-completed:
  - FOUND-01

# Metrics
duration: 3min
completed: 2026-03-13
---

# Phase 01 Plan 01: Project Scaffold and CLI Entry Point Summary

**Hatchling-packaged hms CLI with Typer, Rich dashboard callback, tomllib config reader, and full Wave 0 pytest scaffold (3 real tests passing, 9 xfail stubs collected)**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-13T18:09:47Z
- **Completed:** 2026-03-13T18:13:21Z
- **Tasks:** 2
- **Files modified:** 11

## Accomplishments

- Installable Python package: `pip install -e ".[dev]"` succeeds with all dependencies (typer, rich, peewee, fsrs, pyyaml, pytest)
- `hms` command on PATH; `--help` shows subcommand list, `--version` prints 0.1.0, no-args invokes Rich panel dashboard
- Wave 0 test scaffold complete: `pytest tests/ -v` exits 0 with 3 green (test_cli.py) and 9 xfail stubs (test_init, test_loader, test_scheduler, test_models)

## Task Commits

Each task was committed atomically:

1. **Task 1: Project scaffold, pyproject.toml, and Typer CLI entry point** - `d6b9bf5` (feat)
2. **Task 2: Test scaffold — conftest and all Wave 0 test stubs** - `d4a3306` (feat)

## Files Created/Modified

- `pyproject.toml` - Hatchling build config, entry point `hms = "hms.cli:app"`, dev extras with pytest, pytest ini options
- `src/hms/__init__.py` - Package marker with `__version__ = "0.1.0"`
- `src/hms/cli.py` - Typer app with dashboard callback and stub subcommands (quiz, stats, generate, daemon)
- `src/hms/config.py` - `load_config()` using tomllib, `HMS_HOME` and `CONFIG_PATH` module-level constants
- `src/hms/content/__init__.py` - Namespace package marker for importlib.resources compatibility
- `tests/conftest.py` - `hms_home` fixture with tmp_path isolation and monkeypatching
- `tests/test_cli.py` - 3 real passing tests: help, version, no-args dashboard
- `tests/test_init.py` - 2 xfail stubs for Plan 01-02 (db init, content dir)
- `tests/test_loader.py` - 3 xfail stubs for Plan 01-03 (YAML loading, type validation)
- `tests/test_scheduler.py` - 2 xfail stubs for Plan 01-02 (FSRS review)
- `tests/test_models.py` - 2 xfail stubs for Plan 01-02 (Peewee models)

## Decisions Made

- `requires-python = ">=3.11"` used instead of the plan's `>=3.12` — Python 3.11 is the installed runtime and contains all required stdlib APIs (tomllib, importlib.resources.files). All features work identically.
- `src/hms/content/__init__.py` added to make the content directory a proper namespace package so `importlib.resources.files("hms.content")` resolves correctly in Plan 01-03.
- `[tool.hatch.build.targets.wheel.force-include]` section kept in pyproject.toml even without YAML content files yet — Plan 01-03 will add them and this avoids a pyproject.toml modification then.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created src/hms/content/ before install**
- **Found during:** Task 1 (pip install -e . step)
- **Issue:** `pyproject.toml` had `[tool.hatch.build.targets.wheel.force-include]` pointing to `src/hms/content` which didn't exist — Hatchling raised `FileNotFoundError` during editable install
- **Fix:** Created `src/hms/content/` directory with `__init__.py` before running pip install
- **Files modified:** `src/hms/content/__init__.py` (new file)
- **Verification:** `pip install -e .` exits 0 after creation
- **Committed in:** `d6b9bf5` (Task 1 commit)

**2. [Rule 1 - Bug] Lowered requires-python from >=3.12 to >=3.11**
- **Found during:** Task 1 (pip install verification)
- **Issue:** Plan specified `requires-python = ">=3.12"` but the environment runs Python 3.11.9. The install would fail on the requires-python check.
- **Fix:** Set `requires-python = ">=3.11"` — 3.11 has tomllib and importlib.resources.files(), satisfying all plan requirements
- **Files modified:** `pyproject.toml`
- **Verification:** `pip install -e .` exits 0; all CLI commands work on 3.11
- **Committed in:** `d6b9bf5` (Task 1 commit)

---

**Total deviations:** 2 auto-fixed (1 blocking, 1 bug)
**Impact on plan:** Both fixes necessary for the install to succeed on the actual Python 3.11 runtime. No scope creep.

## Issues Encountered

None beyond the two auto-fixed deviations above.

## User Setup Required

None — no external service configuration required.

## Next Phase Readiness

- Package installable; `hms` entry point on PATH
- All Wave 0 test stubs exist and pytest suite is runnable
- Plan 01-02 can proceed immediately: add `hms/db.py`, `hms/models.py`, `hms/init.py`, `hms/scheduler.py` — xfail stubs in test_init.py, test_scheduler.py, and test_models.py will flip to real assertions
- Plan 01-03 can proceed after 01-02: add `hms/loader.py` and bundled YAML content — xfail stubs in test_loader.py will flip

---

*Phase: 01-foundation*
*Completed: 2026-03-13*
