---
phase: 3
slug: gamification-adaptive-difficulty
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml `[tool.pytest.ini_options]` — testpaths=["tests"], addopts="-x -q" |
| **Quick run command** | `python -m pytest tests/test_gamification.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_gamification.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 3-01-01 | 01 | 0 | GAME-01 | unit | `python -m pytest tests/test_gamification.py::test_xp_formula -x` | ❌ W0 | ⬜ pending |
| 3-01-02 | 01 | 0 | GAME-01 | unit | `python -m pytest tests/test_gamification.py::test_session_xp_accumulation -x` | ❌ W0 | ⬜ pending |
| 3-01-03 | 01 | 0 | GAME-01 | unit | `python -m pytest tests/test_gamification.py::test_streak_multiplier_cap -x` | ❌ W0 | ⬜ pending |
| 3-01-04 | 01 | 1 | GAME-02 | unit | `python -m pytest tests/test_gamification.py::test_streak_consecutive -x` | ❌ W0 | ⬜ pending |
| 3-01-05 | 01 | 1 | GAME-02 | unit | `python -m pytest tests/test_gamification.py::test_streak_resets_no_freeze -x` | ❌ W0 | ⬜ pending |
| 3-01-06 | 01 | 1 | GAME-03 | unit | `python -m pytest tests/test_gamification.py::test_freeze_consumed -x` | ❌ W0 | ⬜ pending |
| 3-01-07 | 01 | 1 | GAME-03 | unit | `python -m pytest tests/test_gamification.py::test_freeze_awarded -x` | ❌ W0 | ⬜ pending |
| 3-01-08 | 01 | 1 | GAME-04 | unit | `python -m pytest tests/test_gamification.py::test_level_derivation -x` | ❌ W0 | ⬜ pending |
| 3-01-09 | 01 | 1 | GAME-04 | unit | `python -m pytest tests/test_gamification.py::test_max_level -x` | ❌ W0 | ⬜ pending |
| 3-02-01 | 02 | 1 | ADAPT-02 | unit | `python -m pytest tests/test_gamification.py::test_tier_locked -x` | ❌ W0 | ⬜ pending |
| 3-02-02 | 02 | 1 | ADAPT-02 | unit | `python -m pytest tests/test_gamification.py::test_tier_unlocked -x` | ❌ W0 | ⬜ pending |
| 3-02-03 | 02 | 1 | ADAPT-03 | unit | `python -m pytest tests/test_gamification.py::test_l3_unlock -x` | ❌ W0 | ⬜ pending |
| 3-02-04 | 02 | 2 | ADAPT-04 | unit | `python -m pytest tests/test_quiz.py::test_build_queue_respects_unlock -x` | ❌ W0 | ⬜ pending |
| 3-02-05 | 02 | 2 | ADAPT-04 | unit | `python -m pytest tests/test_quiz.py::test_unlock_notification -x` | ❌ W0 | ⬜ pending |
| 3-03-01 | 03 | 2 | GAME-05 | unit | `python -m pytest tests/test_cli.py::test_stats_empty -x` | ❌ W0 | ⬜ pending |
| 3-03-02 | 03 | 2 | GAME-05 | unit | `python -m pytest tests/test_cli.py::test_stats_with_data -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_gamification.py` — stubs for GAME-01, GAME-02, GAME-03, GAME-04, ADAPT-02, ADAPT-03, ADAPT-04
- [ ] `tests/conftest.py` — update to include `UserStat` in `db.create_tables()` call
- [ ] `tests/test_cli.py` — stubs for GAME-05 (test_stats_empty, test_stats_with_data)
- [ ] `tests/test_quiz.py` — stubs for ADAPT-04 (test_build_queue_respects_unlock, test_unlock_notification)
- [ ] `src/hms/gamification.py` — new module (can be stub at Wave 0; implemented in Wave 1)
- [ ] `UserStat` table registration in `ensure_initialized()` — `db.create_tables([Card, ReviewHistory, UserStat], safe=True)`

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| `hms` dashboard shows streak + level name + cards due | GAME-05 | Visual terminal output; no assertion on Rich Panel layout | Run `hms` with existing review history; confirm streak line and level name appear |
| Unlock notification appears in session summary | ADAPT-04 | Requires a live session with a mastery threshold being crossed | Manually review 80%+ of L1 cards for a topic; run `hms quiz`; confirm unlock message in summary |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 5s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
