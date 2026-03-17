---
phase: 1
slug: foundation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-13
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — Wave 0 installs |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 1-01-xx | 01 | 1 | FOUND-01 | smoke | `pytest tests/test_cli.py::test_hms_help -x` | ❌ W0 | ⬜ pending |
| 1-02-xx | 02 | 1 | FOUND-02 | integration | `pytest tests/test_init.py::test_first_run_creates_db -x` | ❌ W0 | ⬜ pending |
| 1-02-xx | 02 | 1 | FOUND-06 | unit | `pytest tests/test_scheduler.py::test_review_updates_due -x` | ❌ W0 | ⬜ pending |
| 1-02-xx | 02 | 1 | FOUND-07 | integration | `pytest tests/test_models.py::test_review_history_persisted -x` | ❌ W0 | ⬜ pending |
| 1-03-xx | 03 | 1 | FOUND-03 | unit | `pytest tests/test_loader.py::test_load_bundled_questions -x` | ❌ W0 | ⬜ pending |
| 1-03-xx | 03 | 1 | FOUND-04 | unit | `pytest tests/test_loader.py::test_all_question_types_valid -x` | ❌ W0 | ⬜ pending |
| 1-03-xx | 03 | 1 | FOUND-05 | unit | `pytest tests/test_loader.py::test_missing_base_field_raises -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/conftest.py` — isolated `hms_home` fixture with `tmp_path` + monkeypatch + db init/close
- [ ] `tests/test_cli.py` — stubs for FOUND-01
- [ ] `tests/test_init.py` — stubs for FOUND-02
- [ ] `tests/test_loader.py` — stubs for FOUND-03, FOUND-04, FOUND-05
- [ ] `tests/test_scheduler.py` — stubs for FOUND-06
- [ ] `tests/test_models.py` — stubs for FOUND-07
- [ ] `pytest` added to `[project.optional-dependencies] dev` in `pyproject.toml`
- [ ] `[tool.pytest.ini_options]` section with `testpaths = ["tests"]` in `pyproject.toml`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `pip install -e .` creates `hms` entry point | FOUND-01 | Requires real install environment | Run `pip install -e .` in fresh venv, then `hms --help` |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
