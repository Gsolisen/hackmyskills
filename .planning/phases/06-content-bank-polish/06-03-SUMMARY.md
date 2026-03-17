---
phase: 06-content-bank-polish
plan: 03
subsystem: cli, testing, config
tags: [typer, rich, yaml, toml, cli-commands, content-validation]

requires:
  - phase: 06-01
    provides: kubernetes.yaml and terraform.yaml content with 45+ questions each
  - phase: 06-02
    provides: cicd.yaml, bash.yaml, aws.yaml content files (135 new questions)
provides:
  - hms topics command listing all topics with card counts and unlock status
  - hms import command for validating and importing YAML question files
  - Fully documented config.toml template with all DEFAULT_CONFIG keys
  - Comprehensive test suite for content bank (CONT-01 through CONT-04, EXT-01)
  - CLI tests for topics and import commands (CONT-05, EXT-03)
  - Config documentation test (EXT-02)
affects: []

tech-stack:
  added: []
  patterns:
    - "import command with rollback: copy file, validate, unlink on failure"
    - "config.toml template with inline comments for every setting section"

key-files:
  created:
    - tests/test_content_bank.py
  modified:
    - src/hms/cli.py
    - src/hms/init.py
    - tests/test_cli.py
    - tests/test_init.py
    - src/hms/content/kubernetes.yaml
    - src/hms/content/terraform.yaml
    - src/hms/content/cicd.yaml
    - src/hms/content/bash.yaml
    - src/hms/content/aws.yaml

key-decisions:
  - "topics command uses Rich Table with Topic/Cards/Unlocked columns, compact format per user decision"
  - "import command uses copy-then-validate-then-rollback pattern for atomic file imports"
  - "config.toml template organized as top-level, [quiet_hours], [daemon] sections with 21 comment lines"

patterns-established:
  - "Import rollback: shutil.copy2 then dest.unlink() on validation failure"
  - "Cross-file duplicate detection on import via validate_content_dir()"

requirements-completed: [CONT-05, EXT-01, EXT-02, EXT-03]

duration: 6min
completed: 2026-03-17
---

# Phase 6 Plan 3: CLI Commands, Config Template, and Content Tests Summary

**Added hms topics and hms import CLI commands, expanded config.toml with inline documentation for all settings, and created comprehensive test suite covering content bank validation and extensibility**

## Performance

- **Duration:** 6 min
- **Started:** 2026-03-17T03:20:21Z
- **Completed:** 2026-03-17T03:26:30Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- `hms topics` command lists all 5 topics with card counts and highest unlocked tier using Rich Table
- `hms import` command validates, copies, and syncs YAML files with full rollback on failure (schema errors or duplicates)
- config.toml template expanded from 8 lines to full documented template with [quiet_hours] and [daemon] sections (21 comment lines)
- Created tests/test_content_bank.py with 7 tests covering CONT-01 through CONT-04 and EXT-01
- Added 7 new CLI tests for topics and import commands (including rejection and rollback tests)
- Added test_config_toml_documented verifying all DEFAULT_CONFIG keys present in template
- Full test suite: 115 tests passing

## Task Commits

Each task was committed atomically:

1. **Task 1: Add hms topics and hms import commands to CLI** - `7667f5d` (feat)
2. **Task 2: Expand config.toml template and create all tests** - `069daa7` (feat)

**Plan metadata:** (pending)

## Files Created/Modified
- `src/hms/cli.py` - Added topics() and import_file() commands with Rich output and validation
- `src/hms/init.py` - Expanded _DEFAULT_CONFIG_TOML with [quiet_hours], [daemon] sections and 21 inline comments
- `tests/test_content_bank.py` - New file: 7 tests for content completeness (L1/L2/L3 counts, metadata, uniqueness, drop-in)
- `tests/test_cli.py` - Added 7 tests: topics command, topics discovery, import, import rejection, duplicate rejection, filename collision
- `tests/test_init.py` - Added test_config_toml_documented verifying all config keys and comment count
- `src/hms/content/{kubernetes,terraform,cicd,bash,aws}.yaml` - Fixed uppercase L3 in question IDs to lowercase slug format

## Decisions Made
- topics command uses compact Rich Table format (Topic/Cards/Unlocked columns) per user decision from 06-CONTEXT.md
- import command implements copy-then-validate-then-rollback pattern: copies file first, runs full cross-file validation, unlinks on failure
- config.toml template mirrors all DEFAULT_CONFIG keys exactly, organized in [quiet_hours] and [daemon] sections with friendly inline comments

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Fixed uppercase tier labels in question IDs across all content files**
- **Found during:** Task 2 (full test suite run)
- **Issue:** 25 question IDs contained uppercase `-L3-` (e.g., `k8s-oom-incident-L3-001`) violating the lowercase slug format enforced by test_question_ids_are_slug_format in test_loader.py
- **Fix:** Regex replacement of `-L1-`, `-L2-`, `-L3-` to lowercase `-l1-`, `-l2-`, `-l3-` in all 5 content YAML files
- **Files modified:** src/hms/content/{kubernetes,terraform,cicd,bash,aws}.yaml
- **Verification:** Full test suite (115 tests) passes including test_question_ids_are_slug_format
- **Committed in:** 069daa7 (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (1 bug fix)
**Impact on plan:** Pre-existing content ID format issue from 06-01/06-02 plans. Fix necessary for test suite to pass. No scope creep.

## Issues Encountered
None beyond the auto-fixed deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- Phase 6 is now complete: all 3 plans executed
- Full content bank: 5 topics with 30+ L1, 10+ L2, 5+ L3 cards each
- CLI surface complete: quiz, stats, interrupt, validate-content, topics, import, daemon (start/stop/status)
- Config.toml fully documented with inline comments
- All 115 tests passing
- Project milestone v1.0 ready for final review

---
## Self-Check: PASSED

All files verified present. Both commit hashes (7667f5d, 069daa7) confirmed in git log.

---
*Phase: 06-content-bank-polish*
*Completed: 2026-03-17*
