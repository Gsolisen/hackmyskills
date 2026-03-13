# Roadmap: HackMySkills

## Overview

HackMySkills is built in six phases that mirror its natural dependency structure. The foundation (data model, FSRS scheduling, YAML loading) must exist before anything else can be built on it. The core quiz experience comes next — this is the primary user-facing loop and must feel polished before gamification is layered on top. Gamification and adaptive difficulty are delivered together in Phase 3 since they share the same underlying data (review history, daily tracking, topic mastery state). The interrupt daemon is deferred to Phase 4 because it carries the highest technical risk (Windows process management) and does not block core value. AI question generation in Phase 5 augments the system once the question model is stable. Phase 6 delivers the curated content bank and extensibility plumbing that makes the system independently useful to others.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation** - Project scaffold, SQLite data model, FSRS scheduling engine, YAML question loading (completed 2026-03-13)
- [ ] **Phase 2: Core Quiz** - `hms quiz` command, all four content types, session flow, Rich terminal output
- [ ] **Phase 3: Gamification + Adaptive Difficulty** - XP, streaks, levels, topic unlock progression, `hms stats`
- [ ] **Phase 4: Interrupt Daemon** - APScheduler background daemon, Windows desktop notifications, startup registration
- [ ] **Phase 5: AI Content Generation** - Claude API integration, question staging, duplicate detection, review workflow
- [ ] **Phase 6: Content Bank + Polish** - Curated DevOps question bank, extensibility commands, config documentation

## Phase Details

### Phase 1: Foundation
**Goal**: The data and scheduling infrastructure exists — cards can be loaded from YAML, stored in SQLite, and scheduled by FSRS
**Depends on**: Nothing (first phase)
**Requirements**: FOUND-01, FOUND-02, FOUND-03, FOUND-04, FOUND-05, FOUND-06, FOUND-07
**Success Criteria** (what must be TRUE):
  1. Running `pip install -e .` installs the `hms` command and it responds to `hms --help`
  2. First run creates `~/.hackmyskills/data.db` and loads questions from YAML files without errors
  3. A YAML question file with all four types (flashcard, scenario, command-fill, explain-concept) passes validation
  4. FSRS scheduling calculates a next due date for a card after a review rating is recorded and persists it in SQLite
**Plans**: 3 plans

Plans:
- [ ] 01-01-PLAN.md — Project scaffold, pyproject.toml, Typer CLI entry point, and test scaffold (Wave 0)
- [ ] 01-02-PLAN.md — SQLite data model (Peewee deferred init), FSRS scheduler wrapper, first-run init
- [ ] 01-03-PLAN.md — YAML question loader, bundled kubernetes.yaml + terraform.yaml, schema validation

### Phase 2: Core Quiz
**Goal**: Users can run a focused quiz session that serves due cards across all four question types with a polished terminal experience
**Depends on**: Phase 1
**Requirements**: QUIZ-01, QUIZ-02, QUIZ-03, QUIZ-04, QUIZ-05, QUIZ-06, QUIZ-07, QUIZ-08, QUIZ-09
**Success Criteria** (what must be TRUE):
  1. `hms quiz` starts a session, serves due cards first then new cards, and stops at the daily cap (default 25)
  2. Flashcard questions display prompt, reveal answer on keypress, and record a self-rating (Again / Hard / Good / Easy) that updates FSRS state
  3. Command fill-in questions accept typed input, evaluate it with fuzzy match, and show the correct answer
  4. Session ends with a summary showing cards reviewed, accuracy, XP earned, and current streak
  5. `hms quiz --topic kubernetes` limits the session to Kubernetes cards only
**Plans**: TBD

Plans:
- [ ] 02-01: Session engine — card selection, daily cap, topic filtering
- [ ] 02-02: Flashcard and command-fill question renderers
- [ ] 02-03: Scenario and explain-concept question renderers
- [ ] 02-04: Session summary display

### Phase 3: Gamification + Adaptive Difficulty
**Goal**: Users accumulate XP and streaks that reflect real progress, and harder cards unlock automatically as topics are mastered
**Depends on**: Phase 2
**Requirements**: GAME-01, GAME-02, GAME-03, GAME-04, GAME-05, ADAPT-01, ADAPT-02, ADAPT-03, ADAPT-04
**Success Criteria** (what must be TRUE):
  1. Completing a quiz session awards XP; the amount varies by recall quality (Easy > Good > Hard > Again) and difficulty tier
  2. A daily streak increments after reviewing at least one card; a streak freeze is earned every 7 days and prevents streak loss on one missed day
  3. `hms stats` shows streak, freeze count, current level, XP to next level, cards due, and per-topic performance in a single view
  4. L2 cards for a topic become available only after ≥80% of that topic's L1 cards are mastered; L3 cards unlock after ≥80% of L2
  5. `hms quiz` with no arguments serves a mixed-tier selection matching current unlock status (not only L1 cards)
**Plans**: TBD

Plans:
- [ ] 03-01: XP, streak, freeze, and level system
- [ ] 03-02: Adaptive difficulty unlock logic and tier-aware card selection
- [ ] 03-03: `hms stats` display

### Phase 4: Interrupt Daemon
**Goal**: A background daemon sends desktop notifications at scheduled intervals and opens a one-question mini-session on demand
**Depends on**: Phase 3
**Requirements**: INT-01, INT-02, INT-03, INT-04, INT-05, INT-06
**Success Criteria** (what must be TRUE):
  1. `hms daemon start` launches the background process, registers it in the Windows Startup folder, and survives a system reboot
  2. `hms daemon stop` cleanly terminates the process and removes it from the Startup folder with no orphan processes
  3. A desktop notification appears at the configured interval during work hours; clicking it or running `hms interrupt` opens a one-question terminal session
  4. No notifications appear outside the quiet hours window configured in `config.toml`
  5. Interrupts stop firing once the daily card cap has been reached for the day
**Plans**: TBD

Plans:
- [ ] 04-01: APScheduler daemon process and Windows Startup registration
- [ ] 04-02: desktop-notifier integration and `hms interrupt` mini-session
- [ ] 04-03: Quiet hours, daily cap respect, and daemon lifecycle commands

### Phase 5: AI Content Generation
**Goal**: Users can generate new questions via Claude API, review them in a staging area, and promote approved questions into the active bank
**Depends on**: Phase 1
**Requirements**: AI-01, AI-02, AI-03, AI-04, AI-05
**Success Criteria** (what must be TRUE):
  1. `hms generate --topic kubernetes --count 5` produces 5 valid questions and writes them to a staging YAML file
  2. Generated questions are tagged with `generated_at` timestamp and `source: ai` and conform to the existing question schema
  3. `hms review-generated` presents each staged question one by one and approves or rejects it; approved questions enter the active bank
  4. Running `hms generate` a second time on the same topic does not produce duplicate questions (detected by ID and similar phrasing)
**Plans**: TBD

Plans:
- [ ] 05-01: Claude API client, prompt engineering, and structured JSON output parsing
- [ ] 05-02: Staging file management and `hms review-generated` command
- [ ] 05-03: Duplicate detection logic

### Phase 6: Content Bank + Polish
**Goal**: The tool ships with a complete curated DevOps question bank and is fully extensible without code changes
**Depends on**: Phase 5
**Requirements**: CONT-01, CONT-02, CONT-03, CONT-04, CONT-05, EXT-01, EXT-02, EXT-03
**Success Criteria** (what must be TRUE):
  1. `hms topics` lists all five DevOps topics (Kubernetes, Terraform, CI/CD, bash, AWS) with card counts and unlock status; each topic has ≥30 L1, ≥10 L2, and ≥5 L3 curated cards with version tags and last-verified dates
  2. Dropping a valid YAML file into `~/.hackmyskills/content/` and running `hms` makes its questions available immediately without any code change
  3. `hms import <file.yaml>` validates the file against the question schema and adds passing questions to the active bank, reporting any validation errors
  4. `config.toml` contains inline comments explaining every setting and is human-readable without consulting documentation
**Plans**: TBD

Plans:
- [ ] 06-01: Curated question bank — Kubernetes and Terraform (L1/L2/L3)
- [ ] 06-02: Curated question bank — CI/CD, bash, and AWS fundamentals (L1/L2/L3)
- [ ] 06-03: `hms import` command, `hms topics` command, and config.toml documentation

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation | 3/3 | Complete   | 2026-03-13 |
| 2. Core Quiz | 0/4 | Not started | - |
| 3. Gamification + Adaptive Difficulty | 0/3 | Not started | - |
| 4. Interrupt Daemon | 0/3 | Not started | - |
| 5. AI Content Generation | 0/3 | Not started | - |
| 6. Content Bank + Polish | 0/3 | Not started | - |
