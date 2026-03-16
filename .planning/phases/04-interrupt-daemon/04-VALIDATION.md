---
phase: 4
slug: interrupt-daemon
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-15
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pyproject.toml (existing) |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v` |
| **Estimated runtime** | ~5 seconds |

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
| 4-01-01 | 01 | 1 | INT-01 | unit | `pytest tests/test_daemon.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-02 | 01 | 1 | INT-01 | unit | `pytest tests/test_daemon.py::test_spawn_detached -x -q` | ❌ W0 | ⬜ pending |
| 4-01-03 | 01 | 1 | INT-01 | unit | `pytest tests/test_daemon.py::test_startup_registration -x -q` | ❌ W0 | ⬜ pending |
| 4-02-01 | 02 | 2 | INT-03, INT-04 | unit | `pytest tests/test_daemon.py::test_scheduler_fires -x -q` | ❌ W0 | ⬜ pending |
| 4-02-02 | 02 | 2 | INT-04 | unit | `pytest tests/test_daemon.py::test_interrupt_session -x -q` | ❌ W0 | ⬜ pending |
| 4-03-01 | 03 | 2 | INT-05 | unit | `pytest tests/test_daemon.py::test_quiet_hours -x -q` | ❌ W0 | ⬜ pending |
| 4-03-02 | 03 | 2 | INT-06 | unit | `pytest tests/test_daemon.py::test_daily_cap -x -q` | ❌ W0 | ⬜ pending |
| 4-03-03 | 03 | 2 | INT-02 | unit | `pytest tests/test_daemon.py::test_daemon_stop -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_daemon.py` — stubs for INT-01 through INT-06
- [ ] `src/hms/daemon/__init__.py` — package skeleton
- [ ] `src/hms/daemon/platform/base.py` — DaemonPlatform abstract interface

*Wave 0 must create test file stubs before plan 04-01 begins.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Desktop notification appears on screen | INT-03 | Requires live OS notification system; cannot be mocked in unit tests | Run `hms daemon start`, wait up to `interval_minutes`, verify toast appears |
| Clicking notification opens terminal session | INT-04 | WinRT click callback opens subprocess; not automatable in CI | Click notification, verify new terminal with `hms interrupt` opens |
| Daemon survives reboot | INT-01 | Requires actual system restart | Register via `hms daemon start`, reboot, verify `hms daemon status` shows running |
| No notifications outside quiet hours | INT-05 | Requires time manipulation or waiting | Set `work_hours_start=23:00 work_hours_end=23:01`, verify no notifications fire at current time |
| First-run WinRT permission prompt | INT-03 | OS-level behavior, unverifiable in test suite | Fresh Windows 11 install: `hms daemon start`, check Windows notification settings if no toast appears |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
