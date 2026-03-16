---
phase: 05-ai-content-generation
plan: 01
status: complete
started: 2026-03-16
completed: 2026-03-16
duration_minutes: 15
---

# Plan 05-01: Content Validation Library

## What Was Built

Content validation library with duplicate detection, extended question schema with optional `source` field, `hms validate-content` CLI command, and removal of the obsolete `generate` stub.

## Key Files

### Created
- `src/hms/validation.py` — Validation library with `validate_content_dir()`, `find_duplicates()`, `ContentError`, `DuplicatePair`, `ValidationResult` dataclasses, and >70% Jaccard token-overlap detection
- `tests/test_validation.py` — 10 tests covering source field validation, content dir validation, and duplicate detection (exact ID + token overlap + no false positives)

### Modified
- `src/hms/loader.py` — Added `VALID_SOURCES = {"curated", "ai"}` and optional source field validation in `validate_question()`
- `src/hms/cli.py` — Added `validate-content` command, removed `generate` stub
- `tests/test_loader.py` — Added 3 tests for source field validation (optional, ai valid, invalid raises)
- `tests/test_cli.py` — Added 3 tests for validate-content command and generate removal

## Decisions

- Token overlap threshold set at 0.70 (Jaccard similarity) for duplicate detection
- Source field is optional — missing defaults conceptually to "curated"
- `_tokenize()` filters tokens with length < 2 to reduce noise

## Self-Check: PASSED

All 101 tests pass. `validate-content` CLI command works. `generate` stub removed from help output.
