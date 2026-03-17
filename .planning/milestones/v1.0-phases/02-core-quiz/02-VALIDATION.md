---
phase: 2
slug: core-quiz
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.x |
| **Config file** | `pyproject.toml` `[tool.pytest.ini_options]` — exists from Phase 1 |
| **Quick run command** | `pytest tests/test_quiz.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_quiz.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-01-xx | 01 | 1 | QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-09 | unit | `pytest tests/test_quiz.py::test_quiz_empty_queue tests/test_quiz.py::test_build_queue_order tests/test_quiz.py::test_daily_cap_from_config tests/test_quiz.py::test_build_queue_topic_filter -x -q` | ❌ W0 | ⬜ pending |
| 2-02-xx | 02 | 2 | QUIZ-04, QUIZ-05 | unit (mock readkey) | `pytest tests/test_quiz.py::test_flashcard_flow tests/test_quiz.py::test_command_fill_correct tests/test_quiz.py::test_command_fill_incorrect -x -q` | ❌ W0 | ⬜ pending |
| 2-03-xx | 03 | 2 | QUIZ-06, QUIZ-07 | unit (mock readkey) | `pytest tests/test_quiz.py::test_scenario_flow tests/test_quiz.py::test_explain_concept_flow -x -q` | ❌ W0 | ⬜ pending |
| 2-04-xx | 04 | 3 | QUIZ-08 | unit | `pytest tests/test_quiz.py::test_session_result_accuracy -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_quiz.py` — xfail stubs for all QUIZ-01 through QUIZ-09 test cases
- [ ] `src/hms/quiz.py` — empty module must exist so test imports resolve
- [ ] `readchar>=4.0` added to `[project.dependencies]` in `pyproject.toml`

*(conftest.py and pytest config already exist from Phase 1 — no new gaps)*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `hms quiz` renders a full card in the terminal, clears screen between cards | QUIZ-04 | Rich console rendering can't be fully captured in pytest CliRunner | Run `hms quiz` in real terminal with ≥1 due card; verify screen clears and Panel renders |
| Ctrl-C mid-session saves partial progress | QUIZ-01 | Ctrl-C in subprocess testing is unreliable | Manually start `hms quiz`, press Ctrl-C after 1 card, run `hms` dashboard to confirm streak |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
