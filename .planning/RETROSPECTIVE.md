# Project Retrospective

*A living document updated after each milestone. Lessons feed forward into future planning.*

## Milestone: v1.0 — MVP

**Shipped:** 2026-03-17
**Phases:** 6 | **Plans:** 19 | **Commits:** 97

### What Was Built
- Complete CLI-based DevOps skill trainer with FSRS spaced repetition and 4 question types
- Gamification system (XP, streaks, streak freezes, levels, adaptive difficulty tiers)
- Background interrupt daemon with Windows desktop notifications via winotify
- Content validation pipeline with CI workflow and 225+ curated questions across 5 topics
- Extensible architecture: drop YAML files or use `hms import` for new content

### What Worked
- TDD approach across all phases — xfail stubs in early waves converted to real tests in later waves
- Wave-based parallelization in planning — independent plans executed concurrently (e.g., 02-02 and 02-03, 06-01 and 06-02)
- Early foundation decisions (Peewee deferred init, FSRS wrapper, YAML schema) paid off in later phases
- Typer sub-app pattern for daemon CLI commands kept the main app clean
- WAL mode + separate Console instances avoided concurrency and circular import issues

### What Was Inefficient
- Phase 4 (daemon) required a mid-course pivot from desktop-notifier to winotify — WinRT click callbacks don't work for unpackaged Python apps. Could have been caught with earlier Windows-specific research
- AI-04 and AI-05 requirements were defined around a `hms generate` CLI approach but implementation pivoted to Claude Code session workflow — requirements should have been updated sooner
- Performance metrics in STATE.md only tracked the first plan accurately; later plan durations weren't captured consistently

### Patterns Established
- Handler signature convention: `(card, q_data, session, _readkey=None)` for all question types
- `_render_*_panel()` extraction pattern for testable Rich output
- Content YAML schema with version_tag and last_verified fields for traceability
- Config organized as top-level + `[quiet_hours]` + `[daemon]` sections

### Key Lessons
1. Windows-specific libraries (notifications, startup registration) need hands-on validation early — mock-passing tests don't catch platform quirks
2. When implementation approach diverges from requirements, update requirements immediately rather than at milestone end
3. Curated content quality > quantity — well-crafted L3 scenario questions with embedded CLI output are more valuable than many simple flashcards

### Cost Observations
- Model mix: primarily opus for execution, sonnet for research/planning
- Sessions: ~19 plan execution sessions + research/planning sessions
- Notable: 5-day MVP delivery for a full-featured CLI tool with 3,962 LOC Python

---

## Cross-Milestone Trends

### Process Evolution

| Milestone | Commits | Phases | Key Change |
|-----------|---------|--------|------------|
| v1.0 | 97 | 6 | Initial baseline — TDD + wave parallelization established |

### Cumulative Quality

| Milestone | Python LOC | Files | Question Bank |
|-----------|------------|-------|---------------|
| v1.0 | 3,962 | 102 | 225+ questions, 5 topics |

### Top Lessons (Verified Across Milestones)

1. Platform-specific features need early hands-on validation (winotify pivot)
2. TDD with xfail stubs provides clean wave boundaries and prevents regression
