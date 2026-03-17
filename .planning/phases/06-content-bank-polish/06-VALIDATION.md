---
phase: 6
slug: content-bank-polish
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml (`[tool.pytest.ini_options]`) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~10 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 06-01-01 | 01 | 1 | CONT-01 | unit | `pytest tests/test_content_bank.py::test_l1_count_per_topic -x` | ❌ W0 | ⬜ pending |
| 06-01-02 | 01 | 1 | CONT-02 | unit | `pytest tests/test_content_bank.py::test_l2_count_per_topic -x` | ❌ W0 | ⬜ pending |
| 06-01-03 | 01 | 1 | CONT-03 | unit | `pytest tests/test_content_bank.py::test_l3_count_per_topic -x` | ❌ W0 | ⬜ pending |
| 06-01-04 | 01 | 1 | CONT-04 | unit | `pytest tests/test_content_bank.py::test_metadata_fields -x` | ❌ W0 | ⬜ pending |
| 06-02-01 | 02 | 1 | CONT-01 | unit | `pytest tests/test_content_bank.py::test_l1_count_per_topic -x` | ❌ W0 | ⬜ pending |
| 06-03-01 | 03 | 2 | CONT-05 | unit | `pytest tests/test_cli.py::test_topics_command -x` | ❌ W0 | ⬜ pending |
| 06-03-02 | 03 | 2 | EXT-01 | integration | `pytest tests/test_content_bank.py::test_drop_in_yaml_discovery -x` | ❌ W0 | ⬜ pending |
| 06-03-03 | 03 | 2 | EXT-02 | unit | `pytest tests/test_init.py::test_config_toml_documented -x` | ❌ W0 | ⬜ pending |
| 06-03-04 | 03 | 2 | EXT-03 | unit | `pytest tests/test_cli.py::test_import_command -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_content_bank.py` — stubs for CONT-01 through CONT-04, EXT-01 (content count assertions, metadata checks, drop-in discovery)
- [ ] `tests/test_cli.py::test_topics_command` — covers CONT-05 (new test in existing file)
- [ ] `tests/test_cli.py::test_import_command` — covers EXT-03 (new test in existing file)
- [ ] `tests/test_cli.py::test_import_rejects_invalid` — covers EXT-03 error path
- [ ] `tests/test_cli.py::test_import_rejects_duplicates` — covers EXT-03 duplicate blocking
- [ ] `tests/test_init.py::test_config_toml_documented` — covers EXT-02 (new test in existing file)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Config.toml inline comments are human-readable | EXT-02 | Subjective readability | Open `config.toml`, verify each setting has a comment explaining its purpose |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
