# Requirements: HackMySkills

**Defined:** 2026-03-13
**Core Value:** The habit forms — consistent, non-annoying quizzing that makes a DevOps engineer measurably faster and more confident over time.

## v1 Requirements

### Foundation

- [x] **FOUND-01**: Project scaffolded as a Python 3.12 CLI package installable via `pip install -e .`
- [x] **FOUND-02**: SQLite database initialized at `~/.hackmyskills/data.db` on first run
- [x] **FOUND-03**: Question bank loaded from YAML files in `~/.hackmyskills/content/` (or bundled)
- [x] **FOUND-04**: YAML question schema supports types: flashcard, scenario, command-fill, explain-concept
- [x] **FOUND-05**: Each question has: id, type, topic, difficulty_tier (L1/L2/L3), tags, version_tag, last_verified
- [x] **FOUND-06**: FSRS v6 scheduling engine wraps `fsrs` library — cards scheduled by due date
- [x] **FOUND-07**: Review history persisted per card (rating, timestamp, FSRS state fields)

### Quiz Session

- [x] **QUIZ-01**: `hms quiz` command starts a focused session
- [x] **QUIZ-02**: Session serves due cards first, then new cards up to daily cap (default: 25 cards)
- [x] **QUIZ-03**: Daily cap is configurable in `~/.hackmyskills/config.toml`
- [x] **QUIZ-04**: Flashcard questions display prompt, wait for keypress, then reveal answer with self-rating (Again / Hard / Good / Easy)
- [x] **QUIZ-05**: Command fill-in questions accept typed answer, check with fuzzy match (Levenshtein), show correct answer
- [x] **QUIZ-06**: Scenario questions display situation, accept free-text or multiple-choice answer, show explanation
- [x] **QUIZ-07**: Explain-concept questions prompt user to type explanation, then show model answer for self-rating
- [x] **QUIZ-08**: Session summary shown at end: cards reviewed, accuracy, XP earned, current streak
- [x] **QUIZ-09**: `hms quiz --topic kubernetes` filters session to a specific topic

### Gamification

- [x] **GAME-01**: XP awarded per review — formula tied to recall quality (Easy > Good > Hard > Again) and card difficulty tier
- [x] **GAME-02**: Daily streak tracked — increments when at least 1 card reviewed per calendar day
- [x] **GAME-03**: Streak freeze earned every 7 days — protects streak on one missed day (prevents quit trigger)
- [x] **GAME-04**: Level system based on total XP with visible level name (e.g. "Pipeline Rookie → Container Captain")
- [x] **GAME-05**: `hms stats` shows: current streak, streak freezes, level, XP to next level, cards due, performance by topic

### Adaptive Difficulty

- [x] **ADAPT-01**: Cards tagged L1 (recall), L2 (application), L3 (scenario) — difficulty tier shown during session
- [x] **ADAPT-02**: New cards start at L1; unlock L2 for a topic after mastering ≥80% of L1 cards in that topic
- [x] **ADAPT-03**: L3 cards unlock after mastering ≥80% of L2 cards in a topic
- [x] **ADAPT-04**: `hms quiz` defaults to serving mixed tiers based on unlock status — not just easy cards forever

### Interrupt Mode

- [x] **INT-01**: `hms daemon start` launches background APScheduler process and registers it in Windows Startup folder
- [x] **INT-02**: `hms daemon stop` cleanly stops the daemon and removes from Startup folder
- [x] **INT-03**: Daemon sends a desktop notification at configurable intervals (default: every 90 minutes during work hours)
- [x] **INT-04**: Notification shows a single question — clicking it (or running `hms interrupt`) opens a 1-question mini-session in terminal
- [x] **INT-05**: Quiet hours configurable in config.toml (default: no notifications before 09:00 or after 21:00)
- [x] **INT-06**: Daemon respects daily card cap — stops sending interrupts once daily cap is hit

### AI Content Generation

- [x] **AI-01**: `hms generate --topic <topic> --count <n>` generates n new questions via Claude API
- [x] **AI-02**: Generated questions written to a staging YAML file for user review before entering the active bank
- [x] **AI-03**: Each AI-generated question tagged with `generated_at` timestamp and `source: ai`
- [ ] **AI-04**: `hms review-generated` CLI command to approve/reject staged questions one by one
- [ ] **AI-05**: Duplicate detection before staging (checks existing question IDs and similar phrasing)

### Content Bank

- [x] **CONT-01**: Curated question bank ships with ≥30 L1 cards per topic for: Kubernetes, Terraform, CI/CD, bash, AWS fundamentals
- [x] **CONT-02**: Each topic has at least 10 L2 (application) cards
- [x] **CONT-03**: Each topic has at least 5 L3 (scenario) cards
- [x] **CONT-04**: All curated questions have version_tag and last_verified date
- [ ] **CONT-05**: `hms topics` lists available topics with card counts and unlock status

### Extensibility

- [ ] **EXT-01**: New topics added by dropping a YAML file into the content directory — no code changes needed
- [ ] **EXT-02**: Config file (`config.toml`) is human-readable and documented inline
- [ ] **EXT-03**: `hms import <file.yaml>` validates and imports a question file into the active bank

## v2 Requirements

### Enhanced Gamification
- **GAME-V2-01**: Badges/achievements for milestones (first 7-day streak, first topic mastered, etc.)
- **GAME-V2-02**: Weekly/monthly summary report
- **GAME-V2-03**: FSRS optimizer — personalize scheduling weights from review history

### Multi-skill Expansion
- **EXT-V2-01**: Non-DevOps skill tracks (e.g. system design, networking, security)
- **EXT-V2-02**: Community question packs (import from URL)

### UX Improvements
- **UX-V2-01**: Web UI / TUI dashboard with charts (rich-pixel or textual)
- **UX-V2-02**: macOS / Linux daemon support via launchd / cron

## Out of Scope

| Feature | Reason |
|---------|--------|
| Multi-user / social features | Solo tool; social adds auth complexity without core value |
| Mobile app | CLI-first; mobile is a separate product |
| Real-time collaboration | Not relevant to solo skill training |
| Paid/freemium features | Personal tool, not a product |
| GUI application | CLI is the primary interface by design |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| FOUND-01 | Phase 1: Foundation | Complete |
| FOUND-02 | Phase 1: Foundation | Complete |
| FOUND-03 | Phase 1: Foundation | Complete |
| FOUND-04 | Phase 1: Foundation | Complete |
| FOUND-05 | Phase 1: Foundation | Complete |
| FOUND-06 | Phase 1: Foundation | Complete |
| FOUND-07 | Phase 1: Foundation | Complete |
| QUIZ-01 | Phase 2: Core Quiz | Complete |
| QUIZ-02 | Phase 2: Core Quiz | Complete |
| QUIZ-03 | Phase 2: Core Quiz | Complete |
| QUIZ-04 | Phase 2: Core Quiz | Complete |
| QUIZ-05 | Phase 2: Core Quiz | Complete |
| QUIZ-06 | Phase 2: Core Quiz | Complete |
| QUIZ-07 | Phase 2: Core Quiz | Complete |
| QUIZ-08 | Phase 2: Core Quiz | Complete |
| QUIZ-09 | Phase 2: Core Quiz | Complete |
| GAME-01 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| GAME-02 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| GAME-03 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| GAME-04 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| GAME-05 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| ADAPT-01 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| ADAPT-02 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| ADAPT-03 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| ADAPT-04 | Phase 3: Gamification + Adaptive Difficulty | Complete |
| INT-01 | Phase 4: Interrupt Daemon | Complete |
| INT-02 | Phase 4: Interrupt Daemon | Complete |
| INT-03 | Phase 4: Interrupt Daemon | Complete |
| INT-04 | Phase 4: Interrupt Daemon | Complete |
| INT-05 | Phase 4: Interrupt Daemon | Complete |
| INT-06 | Phase 4: Interrupt Daemon | Complete |
| AI-01 | Phase 5: AI Content Generation | Complete |
| AI-02 | Phase 5: AI Content Generation | Complete |
| AI-03 | Phase 5: AI Content Generation | Complete |
| AI-04 | Phase 5: AI Content Generation | Pending |
| AI-05 | Phase 5: AI Content Generation | Pending |
| CONT-01 | Phase 6: Content Bank + Polish | Complete |
| CONT-02 | Phase 6: Content Bank + Polish | Complete |
| CONT-03 | Phase 6: Content Bank + Polish | Complete |
| CONT-04 | Phase 6: Content Bank + Polish | Complete |
| CONT-05 | Phase 6: Content Bank + Polish | Pending |
| EXT-01 | Phase 6: Content Bank + Polish | Pending |
| EXT-02 | Phase 6: Content Bank + Polish | Pending |
| EXT-03 | Phase 6: Content Bank + Polish | Pending |

**Coverage:**
- v1 requirements: 43 total
- Mapped to phases: 43
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-13*
*Last updated: 2026-03-13 after roadmap creation — individual requirement traceability expanded*
