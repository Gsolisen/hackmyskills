# Research Summary: HackMySkills

**Domain:** CLI-based spaced repetition / adaptive learning tool
**Researched:** 2026-03-13
**Overall confidence:** HIGH (all key libraries verified against current PyPI, official docs, and multiple sources)

---

## Executive Summary

HackMySkills is a well-defined problem with a mature Python ecosystem that covers every requirement. The stack is essentially a composition of proven, independently maintained libraries rather than a custom-built system. Python 3.12 is unambiguously the right language choice: the Windows notification ecosystem (via WinRT), the spaced repetition algorithm library (fsrs), the Claude API SDK, and the terminal UI toolkit (Rich + Typer) are all Python-first and have current, actively-maintained versions.

The spaced repetition algorithm choice is the most consequential technical decision. FSRS (Free Spaced Repetition Scheduler) is the current state-of-the-art — trained on 700M real-world reviews, adopted by Anki in 2023, and delivers 20-30% fewer reviews for equivalent retention compared to the 1987-era SM-2 algorithm. The `fsrs` Python package (v6.3.1, released March 10, 2026) makes this a one-line dependency.

The interrupt-mode (habit-forming popup) feature is achievable on Windows 11 via `desktop-notifier` (WinRT backend) triggered by an `APScheduler` daemon process running in the background. This is the correct architecture — simpler than Windows Task Scheduler and cross-platform. The daemon is started at login via the Windows Startup folder.

Data persistence needs are modest (hundreds to low-thousands of cards, review history, streaks/XP). Peewee ORM with SQLite is correctly sized — lightweight, no server, and Peewee 4.0 (released Feb 2026) is production-stable.

## Key Findings

**Stack:** Python 3.12 + Typer + Rich + fsrs + Peewee/SQLite + anthropic SDK + desktop-notifier + APScheduler

**Architecture:** Single-user CLI tool with a persistent daemon for interrupt scheduling. Local SQLite database at `~/.hackmyskills/data.db`. YAML question bank files. TOML config.

**Critical pitfall:** The interrupt daemon architecture requires careful process management on Windows — a poorly managed daemon can accumulate orphan processes or fail to start on login. The startup/shutdown mechanism needs explicit care in Phase 1.

---

## Implications for Roadmap

Suggested phase structure based on dependency ordering and risk:

1. **Foundation** — Project scaffold, data model, FSRS integration, basic question loading from YAML
   - Addresses: persistence, spaced repetition algorithm, question bank format
   - Rationale: Everything else depends on cards being stored and scheduled correctly. Get the FSRS → Peewee serialization working before building any UI.
   - Avoids: Building quiz UI against a fake/hardcoded scheduling system

2. **Core Quiz Experience** — Typer CLI commands, Rich output, questionary prompts, focused session mode
   - Addresses: CLI framework, interactive prompts, session flow, multiple content types
   - Rationale: The single most important UX piece. Must feel polished before adding gamification on top.

3. **Gamification Layer** — XP, streaks, levels, performance stats, Rich progress displays
   - Addresses: reward/streak/XP system, progress tracking
   - Rationale: Built on top of the data model from Phase 1. Streaks require correct daily review tracking.

4. **Interrupt / Habit Loop** — APScheduler daemon, desktop-notifier popups, startup registration
   - Addresses: scheduled popups, habit-forming interrupts
   - Rationale: Technically the riskiest piece (Windows process management, WinRT permissions). Defer until the quiz itself is solid. Failure here doesn't break core functionality.

5. **AI Content Generation** — Claude API integration, dynamic question generation, gap-filling
   - Addresses: AI-generated questions, extensibility for new tracks
   - Rationale: Enhances the question bank but isn't required for core loop. Depends on Phase 1 question model being stable.

6. **Question Bank + Polish** — Curated DevOps question bank (k8s, Terraform, CI/CD, bash, AWS), full content for all tracks
   - Addresses: curated content, extensibility
   - Rationale: Content can be filled in last; the system should be content-agnostic by this point.

**Phase ordering rationale:**
- Phase 1 before everything: FSRS scheduling and data model are the structural foundation
- Phase 2 before Phase 3: Can't layer gamification on a quiz that doesn't work well
- Phase 4 deferred: Interrupt daemon is independent and risky; doesn't block core value
- Phase 5 deferred: AI generation augments but doesn't define the system
- Phase 6 last: Content is the easiest part to add and can be grown iteratively

**Research flags for phases:**
- Phase 4 (Daemon): Likely needs deeper research — Windows Startup folder registration, APScheduler persistence across restarts, and WinRT notification permissions need validation on a real Windows 11 install
- Phase 5 (AI): Likely needs research into optimal Claude prompting for structured JSON question output, and rate-limit / cost management patterns
- Phases 1-3: Standard patterns, well-documented libraries, unlikely to need additional research

---

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | All library versions verified against PyPI (March 2026). Official sources. |
| Algorithm (FSRS) | HIGH | PyPI confirmed v6.3.1 released March 10, 2026. Algorithm research from Anki official docs and peer-reviewed sources. |
| Notifications | MEDIUM | desktop-notifier v6.2.0 confirmed. Windows WinRT behavior verified from official docs. Actual WinRT permissions flow on Windows 11 not tested — flag for Phase 4. |
| Claude API | HIGH | anthropic SDK v0.84.0 confirmed on PyPI. Official API docs verified. |
| Scheduling / daemon | MEDIUM | APScheduler v3.11.2 confirmed. Daemon architecture is standard pattern but Windows Startup integration has known quirks. |
| Content format (YAML) | HIGH | PyYAML is stdlib-adjacent and uncontroversial. YAML for human-editable content is standard. |

---

## Gaps to Address

- Windows WinRT notification permission flow: needs hands-on validation in Phase 4. The desktop-notifier README notes that first-run behavior varies across Windows builds.
- APScheduler persistence: job store configuration for SQLite needs validation — if the daemon restarts, jobs should not duplicate. Test in Phase 4.
- Claude prompt engineering: optimal prompt structure for generating valid, diverse DevOps quiz questions in structured JSON format — needs experimentation in Phase 5.
- FSRS optimizer: the `fsrs` package includes an optional optimizer component that personalizes weights from review history. Worthwhile to investigate for Phase 3/5 — could make adaptive difficulty much stronger than manual difficulty tiers.
