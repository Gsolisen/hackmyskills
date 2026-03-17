# HackMySkills

## What This Is

A CLI-based DevOps skill trainer that drills knowledge through FSRS spaced repetition, adaptive difficulty tiers, and a habit-forming gamification system. Ships with 225+ curated questions across Kubernetes, Terraform, CI/CD, bash, and AWS. Background daemon sends desktop notifications at configurable intervals for micro-learning interrupts throughout the workday.

## Core Value

The habit forms: the user gets quizzed consistently, sees their streak grow, and notices they're actually getting faster and more confident on topics they used to struggle with.

## Requirements

### Validated

- ✓ CLI tool installable via pip, runs on Windows (cross-platform Python) — v1.0
- ✓ FSRS v6 spaced repetition surfaces weak areas more frequently — v1.0
- ✓ Adaptive difficulty with 3 tiers (L1→L2→L3), unlocking based on mastery — v1.0
- ✓ XP/streak/level system with streak freezes for dopamine feedback loop — v1.0
- ✓ Background daemon with Windows desktop notifications for learning interrupts — v1.0
- ✓ Focused session mode (`hms quiz`) with topic filtering and daily cap — v1.0
- ✓ 4 content types: flashcard, scenario, command-fill, explain-concept — v1.0
- ✓ Curated 225+ question bank across 5 DevOps topics — v1.0
- ✓ Content validation and Claude Code workflow for AI-assisted question generation — v1.0
- ✓ Extensible via YAML files and `hms import` command — v1.0
- ✓ `hms stats` with streak, level, XP, per-topic performance — v1.0

### Active

- [ ] Badges/achievements for milestones (first 7-day streak, first topic mastered)
- [ ] Weekly/monthly summary report
- [ ] FSRS optimizer — personalize scheduling weights from review history
- [ ] Non-DevOps skill tracks (system design, networking, security)
- [ ] Community question packs (import from URL)
- [ ] Web UI / TUI dashboard with charts
- [ ] macOS / Linux daemon support via launchd / cron

### Out of Scope

- Mobile app — CLI-first; mobile is a separate product
- Multi-user / social features — solo tool; social adds auth complexity without core value
- Real-time collaboration — not relevant to solo skill training
- Paid/freemium features — personal tool, not a product

## Context

Shipped v1.0 with 3,962 LOC Python across 102 files in 5 days.
Tech stack: Python 3.11+, Typer, Rich, Peewee/SQLite, fsrs 6.3.1, winotify, APScheduler 3.x, PyYAML.
Desktop daemon uses winotify (not desktop-notifier) — WinRT click callbacks don't work for unpackaged Python apps.
Content bank uses YAML with schema validation; CI workflow enforces quality on PRs.

## Constraints

- **Platform**: Windows 11 primary, cross-platform Python (3.11+)
- **Interface**: CLI-first; Windows desktop notifications for interrupt mode
- **AI**: Claude API for dynamic question generation (via Claude Code sessions)
- **Extensibility**: Content in YAML files; `hms import` validates and adds to active bank

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| CLI-first interface (Typer + Rich) | Fits naturally in a DevOps workflow | ✓ Good — clean UX, Rich panels |
| FSRS v6 spaced repetition | Best retention algorithm, actively maintained | ✓ Good — works well with Peewee |
| Curated bank + AI generation guide | Guarantees quality baseline + infinite variety | ✓ Good — 225+ cards shipped |
| Peewee ORM + SQLite | Lightweight, zero-config, single-file DB | ✓ Good — WAL mode handles concurrent daemon access |
| winotify over desktop-notifier | WinRT click callbacks fail for unpackaged apps | ✓ Good — bat-file launch target works |
| APScheduler 3.x (not 4.x) | 4.x has breaking API changes, in-memory job store sufficient | ✓ Good — BackgroundScheduler is simple |
| YAML content files | Human-readable, extensible, CI-validatable | ✓ Good — schema validation catches errors |
| Adaptive difficulty (L1→L2→L3) | Prevents easy-card-forever loop, rewards mastery | ✓ Good — 80% threshold feels right |
| Streak freezes every 7 days | Prevents quit trigger from single missed day | ✓ Good — Duolingo-inspired retention mechanic |
| Claude Code session workflow for AI content | More flexible than CLI generate command | ✓ Good — generation guide provides structure |

---
*Last updated: 2026-03-17 after v1.0 milestone*
