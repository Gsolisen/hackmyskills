---
phase: 01-foundation
plan: 03
subsystem: content
tags: [yaml, pyyaml, importlib-resources, question-bank, validation]

# Dependency graph
requires:
  - phase: 01-01
    provides: src-layout with hatchling, hms.content package namespace, pyproject.toml force-include
  - phase: 01-02
    provides: loader.py referenced from init.py _copy_bundled_content()
provides:
  - "load_questions(path) -> list[dict]: loads and validates YAML question files"
  - "validate_question(q) raises ValueError on missing base/type fields"
  - "VALID_TYPES, REQUIRED_BASE_FIELDS, TYPE_REQUIRED_FIELDS constants"
  - "get_bundled_content_files(): yields Traversable objects for bundled YAMLs"
  - "kubernetes.yaml: 6 bundled questions covering all four types"
  - "terraform.yaml: 6 bundled questions covering all four types"
  - "FOUND-03, FOUND-04, FOUND-05 test coverage (9 tests green)"
affects:
  - 02-quiz-engine
  - 03-cli-commands

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "yaml.safe_load() only (never yaml.load()) for security"
    - "importlib.resources.files() Traversable pattern for bundled package data"
    - "Validation at load time — validate_question() raises ValueError with field names in message"
    - "TYPE_REQUIRED_FIELDS dispatch dict for type-specific field validation"

key-files:
  created:
    - src/hms/loader.py
    - src/hms/content/kubernetes.yaml
    - src/hms/content/terraform.yaml
  modified:
    - tests/test_loader.py

key-decisions:
  - "load_questions() accepts both Path and importlib.resources Traversable via hasattr(path, 'read_bytes') duck-typing"
  - "Both YAML files include all four question types so a single file can verify full schema coverage in tests"
  - "validate_question() validates tier against VALID_TIERS set — L1/L2/L3 only"
  - "_copy_bundled_content() in init.py was already implemented correctly in Plan 01-02 — no changes needed"

patterns-established:
  - "Pattern: YAML question schema — base fields + type-specific dispatch; all validated at load time"
  - "Pattern: bundled content via importlib.resources.files('hms.content').iterdir() — works after pip install -e ."

requirements-completed: [FOUND-03, FOUND-04, FOUND-05]

# Metrics
duration: 8min
completed: 2026-03-13
---

# Phase 1 Plan 3: YAML Question Loader Summary

**YAML loader with base-field and type-specific validation, kubernetes.yaml and terraform.yaml bundled question files covering all four question types, 9 real tests replacing xfail stubs**

## Performance

- **Duration:** 8 min
- **Started:** 2026-03-13T21:21:00Z
- **Completed:** 2026-03-13T21:23:51Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments

- loader.py with load_questions(), validate_question(), VALID_TYPES, REQUIRED_BASE_FIELDS, TYPE_REQUIRED_FIELDS, get_bundled_content_files()
- 6 bundled kubernetes.yaml questions covering all four types (flashcard, command-fill, scenario, explain-concept)
- 6 bundled terraform.yaml questions covering all four types
- 9 real test assertions replacing xfail stubs — full suite 21 passed

## Task Commits

Each task was committed atomically:

1. **Task 1: YAML loader with validation and bundled question files** - `11a6795` (feat)
2. **Task 2: Fill in test_loader.py stubs with real assertions** - `35b853a` (feat)

**Plan metadata:** (docs commit below)

## Files Created/Modified

- `src/hms/loader.py` - load_questions(), validate_question(), VALID_TYPES, REQUIRED_BASE_FIELDS, TYPE_REQUIRED_FIELDS constants, get_bundled_content_files()
- `src/hms/content/kubernetes.yaml` - 6 bundled questions: 3 flashcard, 1 command-fill, 1 scenario, 1 explain-concept
- `src/hms/content/terraform.yaml` - 6 bundled questions: 3 flashcard, 1 command-fill, 1 scenario, 1 explain-concept
- `tests/test_loader.py` - 9 real tests, all xfail markers removed

## Decisions Made

- load_questions() uses duck-typing `hasattr(path, 'read_bytes')` to accept both filesystem Path and importlib.resources Traversable — no separate overloads needed
- Both YAML files include all four question types so test_all_question_types_valid can verify full schema coverage from a single file
- _copy_bundled_content() in init.py was already a complete implementation from Plan 01-02 — no changes needed for this plan
- Tier validation against VALID_TIERS = {"L1", "L2", "L3"} added to validate_question() as specified in plan action

## Deviations from Plan

None - plan executed exactly as written. The _copy_bundled_content() stub in init.py was already a real implementation (not a stub) from Plan 01-02, so no update was needed there.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 1 foundation complete: hms CLI, SQLite data model, FSRS scheduler, YAML loader, bundled content
- All 21 tests green across Plans 01-01, 01-02, 01-03
- Phase 2 (quiz engine) can import load_questions() from hms.loader and FSRS from hms.scheduler

---
*Phase: 01-foundation*
*Completed: 2026-03-13*
