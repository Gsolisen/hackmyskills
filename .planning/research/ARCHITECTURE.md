# Architecture Patterns

**Domain:** CLI-based spaced repetition / adaptive skill trainer
**Researched:** 2026-03-13
**Confidence:** HIGH (core structure), MEDIUM (daemon/interrupt on Windows)

---

## Recommended Architecture

The system has six coherent layers. Each layer has a single owner and communicates
with adjacent layers only — no layer reaches across two levels.

```
┌──────────────────────────────────────────────────────────┐
│                      CLI Layer                           │
│   Typer commands: quiz, session, stats, config, setup    │
│   Rich for rendering tables, progress, prompts           │
└──────────────┬───────────────────────────────────────────┘
               │ calls
┌──────────────▼───────────────────────────────────────────┐
│                   Session Engine                         │
│   Drives an active quiz session: question selection,     │
│   answer evaluation, XP/streak updates, session summary  │
└───────┬──────────────────────────┬───────────────────────┘
        │ reads/writes             │ calls
┌───────▼──────────┐    ┌──────────▼──────────────────────┐
│  Scheduler /     │    │        Content Store            │
│  SRS Engine      │    │  Questions, topics, difficulty  │
│  (FSRS via       │    │  levels — loaded from YAML/JSON │
│  py-fsrs)        │    │  files or SQLite, never from    │
│                  │    │  application code               │
└───────┬──────────┘    └──────────┬──────────────────────┘
        │ persists to              │ persists to
┌───────▼──────────────────────────▼──────────────────────┐
│                   Progress Store (SQLite)                │
│  Cards table, review log, session history, XP/streaks   │
│  Single file: ~/.hackmyskills/progress.db               │
└──────────────────────────────────────────────────────────┘
               │
┌──────────────▼───────────────────────────────────────────┐
│             AI Generation Layer (optional path)          │
│  Claude API — generates new questions on demand or       │
│  during a background refresh cycle. Results written      │
│  back to Content Store, not served live in a session.    │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│               Interrupt Daemon (separate process)        │
│  Windows Task Scheduler fires `hms interrupt` every N   │
│  minutes. Command fires a toast notification, then exits.│
│  Does NOT stay resident. Reads only due-card count from  │
│  Progress Store. Writing happens in CLI Layer sessions.  │
└──────────────────────────────────────────────────────────┘
```

---

## Component Boundaries

| Component | Responsibility | Reads From | Writes To |
|-----------|---------------|------------|-----------|
| CLI Layer | Parse commands, render UI, collect user input | Session Engine results, Progress Store (stats) | nothing directly |
| Session Engine | Drive a quiz session start-to-finish | Content Store, Progress Store | Progress Store (results) |
| SRS Engine | Compute next review dates, prioritize weak cards | Progress Store (card state) | Progress Store (updated card state) |
| Content Store | Provide questions filtered by topic/difficulty | YAML/JSON content files | nothing (read-only at runtime) |
| Progress Store | Persist all mutable state | SQLite file | SQLite file |
| AI Generation Layer | Generate new questions via Claude API | Content Store (for dedup context), env (API key) | Content Store (new YAML/JSON files) |
| Interrupt Daemon | Fire review reminders at intervals | Progress Store (due count only) | nothing — fires OS notification then exits |

**Key rule:** The Interrupt Daemon is read-only and stateless. It never writes to
the Progress Store. All writes happen inside explicitly-started sessions.

---

## Data Flow

### Active Session Flow

```
User runs: hms quiz --topic kubernetes

CLI Layer
  └─► Session Engine: start_session(topic, mode)
        └─► SRS Engine: get_due_cards(topic, limit=10)
              └─► Progress Store: SELECT cards WHERE due <= now AND topic = ?
              ◄── returns ranked Card list
        └─► Content Store: fetch_questions(card_ids)
              └─► YAML/JSON files: load question text, options, explanations
              ◄── returns Question objects
        ◄── returns Session(questions)

  [for each question]
  CLI Layer: render question → collect answer → record response time
  └─► Session Engine: evaluate_answer(card_id, rating)
        └─► SRS Engine: review_card(card, rating)  [py-fsrs API]
              ◄── returns updated Card + ReviewLog
        └─► Progress Store: UPDATE card, INSERT review_log
        └─► XP/Streak logic: calculate delta, UPDATE progress

CLI Layer: render session summary (XP earned, streak, topics reviewed)
```

### Interrupt Daemon Flow

```
Windows Task Scheduler fires: python -m hackmyskills.daemon interrupt

Interrupt Daemon
  └─► Progress Store: SELECT COUNT(*) FROM cards WHERE due <= now
  ◄── returns N

  if N > 0:
    └─► winotify: toast("HackMySkills", f"{N} cards due — run hms quiz")
        [optional action button launches terminal with `hms quiz`]

  process exits (no long-running background process)
```

### AI Question Generation Flow

```
User runs: hms generate --topic terraform --count 20

AI Generation Layer
  └─► Content Store: read existing questions for topic (dedup context)
  └─► Claude API: POST /messages with structured output schema
        ◄── returns List[QuestionSchema] (Pydantic, via structured outputs beta)
  └─► Validate + deduplicate against existing content
  └─► Content Store: write new YAML file (e.g., content/terraform/ai_generated.yaml)
  └─► Progress Store: INSERT new card stubs (state=Learning, due=now)

CLI Layer: "Generated 18 new questions for terraform"
```

---

## Interrupt Daemon on Windows

**Decision: Windows Task Scheduler, not a long-running resident process.**

Rationale:
- A resident daemon process requires startup management, crash recovery, and
  user-visible tray icon — significant complexity for V1.
- Windows Task Scheduler is built into every Windows installation, requires no
  dependencies, and survives reboots automatically.
- The "daemon" is actually just the CLI itself invoked by the scheduler: a
  `hms interrupt` sub-command that reads one SQLite query, fires one toast, and exits.
- This architecture is also cross-platform: macOS uses `launchd`, Linux uses
  `cron` — the setup command (`hms setup-daemon`) writes the appropriate
  scheduler entry for the detected OS.

**Windows-specific implementation:**

```
hms setup-daemon --interval 90  (minutes between interrupts)
  └─► win32com.client (or schtasks.exe subprocess) registers:
      Task name: HackMySkills-Interrupt
      Trigger:   Repeat every 90 minutes, start on login, run while user is logged on
      Action:    pythonw.exe -m hackmyskills.daemon interrupt
      Condition: Only when idle for ≥ 2 minutes (avoids interrupting active work)
```

Notification library: **winotify** (Windows 10/11 toast, no dependencies beyond
PowerShell). Falls back to `plyer` for macOS/Linux.

---

## Content Storage Format

Questions live in YAML files, not in the database. The database stores only card
state (scheduling metadata). This means content is version-controllable, editable
with any text editor, and can be contributed via PR.

```
content/
  kubernetes/
    basics.yaml
    advanced.yaml
    ai_generated.yaml   ← written by hms generate
  terraform/
    ...

content/kubernetes/basics.yaml (example):
---
- id: k8s-001
  type: flashcard
  topic: kubernetes
  subtopic: pods
  difficulty: 1          # 1=easy, 2=medium, 3=hard
  question: "What is the smallest deployable unit in Kubernetes?"
  answer: "A Pod — one or more containers sharing network/storage."
  tags: [core-concepts, pods]

- id: k8s-002
  type: command-fill
  topic: kubernetes
  subtopic: kubectl
  difficulty: 2
  prompt: "List all pods in namespace 'prod' with wide output:"
  answer: "kubectl get pods -n prod -o wide"
  tags: [kubectl, namespaces]
```

Card state in SQLite stores only: `card_id` (FK to YAML id), `due`, `stability`,
`difficulty`, `state`, `reps`, `lapses`. Content is never duplicated into the DB.

---

## Progress Store Schema (SQLite)

```sql
-- Core SRS state (maps to py-fsrs Card fields)
CREATE TABLE cards (
    card_id     TEXT PRIMARY KEY,   -- matches YAML id (e.g., "k8s-001")
    topic       TEXT NOT NULL,
    due         DATETIME NOT NULL,
    stability   REAL,
    difficulty  REAL,
    elapsed_days INTEGER DEFAULT 0,
    scheduled_days INTEGER DEFAULT 0,
    reps        INTEGER DEFAULT 0,
    lapses      INTEGER DEFAULT 0,
    state       INTEGER DEFAULT 0,  -- 0=Learning, 1=Review, 2=Relearning
    last_review DATETIME,
    created_at  DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Full review history for analytics
CREATE TABLE review_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    card_id     TEXT NOT NULL,
    rating      INTEGER NOT NULL,   -- 1=Again 2=Hard 3=Good 4=Easy
    review_time DATETIME NOT NULL,
    response_ms INTEGER,            -- how long user took to answer
    state_before INTEGER,
    state_after  INTEGER,
    scheduled_days INTEGER
);

-- Session-level summaries (for streaks, XP)
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  DATETIME NOT NULL,
    ended_at    DATETIME,
    topic       TEXT,
    cards_reviewed INTEGER DEFAULT 0,
    correct     INTEGER DEFAULT 0,
    xp_earned   INTEGER DEFAULT 0
);

-- Gamification state
CREATE TABLE profile (
    key         TEXT PRIMARY KEY,
    value       TEXT NOT NULL       -- JSON-encoded for flexibility
);
-- Keys: "total_xp", "current_streak", "longest_streak", "last_session_date"
```

---

## Suggested Build Order

The build order follows strict dependency direction: nothing can be built if the
thing it depends on doesn't exist yet.

```
1. Progress Store (SQLite schema + migration runner)
   └── Needed by: everything else that reads or writes state

2. Content Store (YAML loader + question model)
   └── Needed by: Session Engine, AI Generation Layer

3. SRS Engine (py-fsrs wrapper, card state transitions)
   └── Needed by: Session Engine (can't pick questions without due-date logic)

4. Session Engine (question selection, answer eval, XP/streak)
   └── Needed by: CLI Layer (session command)

5. CLI Layer — basic commands (hms quiz, hms stats, hms config)
   └── Needed by: users; first end-to-end usable product

6. Interrupt Daemon + setup-daemon command
   └── Needs: Progress Store (due count), CLI Layer (the interrupt sub-command)
   └── Note: Can be deferred past MVP; manual `hms quiz` is sufficient V1

7. AI Generation Layer (Claude API integration)
   └── Needs: Content Store (write path), working question model
   └── Note: Defer until curated content bank is proven to work
```

**Phase implication:** Phases 1-5 deliver a fully functional product (curated content,
sessions, tracking). Phase 6 adds interrupt habit loop. Phase 7 adds AI expansion.

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Daemon as Resident Process

**What it is:** A long-running Python process that wakes on a timer.
**Why bad on Windows:** No standard way to install/uninstall without a service
framework (NSSM, pywin32 service). Crashes silently, does not restart on reboot
without additional scaffolding. Adds complexity with no benefit over Task Scheduler.
**Instead:** Use Windows Task Scheduler (see above). The daemon is invoked, runs for
~1 second, and exits.

### Anti-Pattern 2: Questions Stored in the Database

**What it is:** INSERT all question text into SQLite at install time; content is
not in files.
**Why bad:** Makes content non-editable without SQL, non-versionable, non-shareable.
AI-generated content has nowhere natural to land.
**Instead:** YAML/JSON files are the source of truth. SQLite stores only scheduling
metadata keyed on the YAML `id` field.

### Anti-Pattern 3: Calling Claude API During a Session

**What it is:** When a question is needed, call Claude to generate one on the fly.
**Why bad:** Adds 1-3 second latency to every question, burns API tokens
unpredictably, fails when offline.
**Instead:** AI generation is a separate, explicit command (`hms generate`) that
pre-populates the content bank. Sessions are always fully offline.

### Anti-Pattern 4: Monolithic CLI Module

**What it is:** All logic in one `cli.py` file.
**Why bad:** Session logic, SRS math, and file I/O become entangled; untestable.
**Instead:** CLI Layer is a thin adapter (Typer commands). All logic lives in
Session Engine and SRS Engine modules that have no Typer dependency.

---

## Scalability Considerations

| Concern | For a single user (this app) | If multi-user ever considered |
|---------|------------------------------|-------------------------------|
| Question volume | YAML files + SQLite handles 10,000+ cards trivially | Move to PostgreSQL, serve YAML from S3 |
| Session concurrency | N/A — single user | Session isolation per user_id FK |
| AI cost | Generate in batches; cache results in YAML | Per-user generation budgets |
| Content updates | Edit YAML files; run `hms sync-content` | Content versioning, schema migration |
| Notification scale | One Task Scheduler task | Push service (out of scope) |

---

## Technology Choices (Architecture Implications)

| Technology | Why (architecture relevance) |
|------------|------------------------------|
| Python 3.11+ | py-fsrs requires 3.10+; Typer + Rich ecosystem; Windows-native |
| Typer + Rich | CLI Layer stays thin; Rich panels separate presentation from logic |
| py-fsrs (FSRS v6) | Modern SRS algorithm; JSON-serializable Card/ReviewLog → SQLite-friendly |
| SQLite (stdlib sqlite3) | Zero-dependency; single file; perfect for single-user desktop app |
| YAML (PyYAML) | Human-editable content files; version-controllable |
| winotify | Windows 10/11 toast notifications; pure Python; no COM dependency |
| win32com / schtasks.exe | Task Scheduler setup; schtasks.exe preferred (no extra install) |
| Anthropic Python SDK | Claude API; structured outputs (Pydantic) for reliable question JSON |

---

## Sources

- [py-fsrs GitHub — FSRS v6 Python implementation](https://github.com/open-spaced-repetition/py-fsrs)
- [open-spaced-repetition/sm-2 — SM-2 Python package](https://github.com/open-spaced-repetition/sm-2)
- [winotify PyPI — Windows toast notifications](https://pypi.org/project/winotify/)
- [Windows-Toasts PyPI](https://pypi.org/project/Windows-Toasts/)
- [Typer GitHub — CLI framework](https://github.com/fastapi/typer)
- [Hashcards: plain-text SRS design analysis](https://borretti.me/article/hashcards-plain-text-spaced-repetition)
- [clsr — JSON-based CLI spaced repetition](https://github.com/adamkpickering/clsr)
- [drill — CLI SRS tool (Python)](https://github.com/rr-/drill)
- [Claude API Structured Outputs docs](https://docs.claude.com/en/docs/build-with-claude/structured-outputs)
- [Windows Task Scheduler Python (win32com)](https://github.com/786raees/task-scheduler-python)
- [Python packaging — entry points guide](https://packaging.python.org/en/latest/guides/creating-command-line-tools/)
- [Typer + Rich CLI patterns (2026)](https://dasroot.net/posts/2026/01/building-cli-tools-with-typer-and-rich/)
