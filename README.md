# HackMySkills

A CLI-based DevOps skill trainer that drills knowledge through spaced repetition, adaptive difficulty, and a habit-forming gamification system. Think Duolingo for DevOps engineers.

Ships with **245+ curated questions** across Kubernetes, Terraform, CI/CD, Bash, and AWS.

## Requirements

- Python 3.11+
- Windows 11 (daemon notifications are Windows-only; quiz works cross-platform)

## Installation

```bash
git clone https://github.com/Gsolisen/hackmyskills.git
cd hackmyskills
pip install -e .
```

First run creates `~/.hackmyskills/` with your database and config.

## Quick Start

```bash
hms                # Dashboard — streak, level, cards due
hms quiz           # Start a quiz session (25 cards)
hms stats          # See your performance
```

---

## Commands

### `hms`

Shows your dashboard: current streak, level, total XP, and cards due today. On first run, displays a welcome message.

```bash
hms
hms --version      # Show version
```

### `hms quiz`

Start a focused quiz session. Due cards appear first, then new cards, up to the daily cap.

```bash
hms quiz                       # All topics, default 25 cards
hms quiz --topic kubernetes    # Only Kubernetes cards
hms quiz -t terraform          # Short flag
```

### `hms stats`

Detailed performance view: streak, level, XP progress, and a per-topic table showing due cards, mastery percentage, and highest unlocked tier.

```bash
hms stats
```

### `hms topics`

Lists all available topics with card counts and unlock status.

```bash
hms topics
```

### `hms validate-content`

Validates all YAML content files against the question schema and checks for duplicates (exact ID match and >70% token overlap). Exits with code 1 if errors found.

```bash
hms validate-content
```

### `hms import <file>`

Validates a YAML question file and imports it into your active content bank.

```bash
hms import my-questions.yaml
```

### `hms interrupt`

Runs a single-question mini-session. Used by the daemon when you click a notification, but you can run it manually too.

```bash
hms interrupt
```

### `hms daemon start`

Launches the background daemon that sends desktop notifications at a configurable interval. Registers itself in the Windows Startup folder so it survives reboots.

```bash
hms daemon start
```

### `hms daemon stop`

Stops the daemon and removes it from Windows Startup.

```bash
hms daemon stop
```

### `hms daemon status`

Check if the daemon is currently running.

```bash
hms daemon status
```

---

## Question Types

| Type | How It Works | Difficulty |
|------|-------------|------------|
| **Flashcard** | See a prompt, press any key to reveal the answer, then self-rate 1-4 | L1 mostly |
| **Command Fill** | Type the command/answer, checked against the correct answer | L1-L2 |
| **Scenario** | Read a situation, type your answer, then compare against the model answer and self-rate | L2-L3 |
| **Explain Concept** | Type your explanation of a concept, then see the model answer and self-rate | L2-L3 |

### Rating Scale

After each question, rate your recall:

| Key | Rating | Meaning |
|-----|--------|---------|
| `1` | Again | Didn't know it |
| `2` | Hard | Struggled but got there |
| `3` | Good | Knew it with some effort |
| `4` | Easy | Instant recall |

The FSRS algorithm uses your ratings to schedule when each card comes back. Cards you struggle with appear more frequently.

---

## Topics & Content

### Bundled Topics (v1.0)

| Topic | Cards | Versions |
|-------|-------|----------|
| Kubernetes | 63 | k8s-1.29 |
| Terraform | 47 | tf-1.7 |
| CI/CD | 45 | GitHub Actions v4 |
| Bash | 45 | — |
| AWS | 45 | — |

### Difficulty Tiers

- **L1 (Recall)** — Basic knowledge. Available immediately.
- **L2 (Application)** — Apply knowledge to real situations. Unlocks after mastering 80% of L1 cards in a topic.
- **L3 (Scenario)** — Production incidents and complex reasoning. Unlocks after mastering 80% of L2 cards.

A card is "mastered" when FSRS moves it to the **Review** state (you've demonstrated consistent recall).

### Adding Your Own Questions

Drop a YAML file into `~/.hackmyskills/content/` or use the import command:

```bash
hms import my-questions.yaml
```

**YAML format:**

```yaml
questions:
  - id: my-topic-subtopic-001
    type: flashcard          # flashcard | command-fill | scenario | explain-concept
    topic: my-topic
    tier: L1                 # L1 | L2 | L3
    tags: [networking, dns]
    version_tag: v1.0
    last_verified: "2026-03-18"
    front: "What does DNS stand for?"
    back: "Domain Name System"
```

**Type-specific fields:**

```yaml
# Flashcard
front: "Question"
back: "Answer"

# Command Fill
prompt: "How do you list all pods?"
command: "kubectl get pods"
accept_partial: true

# Scenario
situation: "A pod is CrashLooping..."
question: "What is your first step?"
answer: "Check the logs with kubectl logs --previous"
explanation: "The --previous flag shows the last crashed container's logs."

# Explain Concept
concept: "Explain how Kubernetes Services route traffic"
model_answer: "Services use label selectors to..."
```

**Required fields for all questions:** `id`, `type`, `topic`, `tier`, `tags`, `version_tag`, `last_verified`

Always run `hms validate-content` after adding questions to check for schema errors and duplicates.

---

## Gamification

### XP System

XP is earned per card based on **tier**, **rating**, and **streak**:

| Tier | Base XP |
|------|---------|
| L1 | 5 |
| L2 | 10 |
| L3 | 20 |

| Rating | Multiplier |
|--------|-----------|
| Again (1) | 0x (no XP) |
| Hard (2) | 0.5x |
| Good (3) | 1.0x |
| Easy (4) | 1.5x |

**Streak bonus:** +10% per 7-day milestone, up to +50% at 35+ days.

**Example:** L2 card, rated Good, 14-day streak = 10 x 1.0 x 1.2 = **12 XP**

### Levels

500 XP per level. 10 levels total:

| Level | Name | XP Required |
|-------|------|-------------|
| 1 | Pipeline Rookie | 0 |
| 2 | Container Cadet | 500 |
| 3 | YAML Wrangler | 1,000 |
| 4 | CI Operator | 1,500 |
| 5 | Cloud Apprentice | 2,000 |
| 6 | Terraform Tinkerer | 2,500 |
| 7 | Cluster Admin | 3,000 |
| 8 | SRE Initiate | 3,500 |
| 9 | Container Captain | 4,000 |
| 10 | DevOps Architect | 4,500 |

### Streaks & Freezes

- **Streak** increments each calendar day you review at least 1 card.
- **Streak freeze** is earned every 7-day streak milestone (day 7, 14, 21...).
- A freeze **automatically protects** your streak if you miss one day. No action needed.
- Freezes stack — you can accumulate multiple.

---

## Configuration

Edit `~/.hackmyskills/config.toml`:

```toml
# Maximum cards per quiz session (default: 25)
daily_cap = 25

# Daemon notification interval in minutes (default: 90)
interval_minutes = 90

# Quiet hours — no notifications outside this window
[quiet_hours]
start = "09:00"
end = "21:00"

# Background daemon settings
[daemon]
interval_minutes = 90           # Minutes between notifications
work_hours_start = "09:00"      # Notifications start time
work_hours_end = "21:00"        # Notifications end time
daily_cap = 10                  # Max interrupt reviews per day
```

### Common Tweaks

| Want to... | Change |
|------------|--------|
| Fewer notifications | `[daemon] interval_minutes = 180` (every 3 hours) |
| Longer sessions | `daily_cap = 50` |
| Later quiet hours | `[quiet_hours] end = "23:00"` |
| Fewer daemon interrupts | `[daemon] daily_cap = 5` |

After changing daemon settings, restart it:

```bash
hms daemon stop
hms daemon start
```

---

## Data Storage

Everything lives in `~/.hackmyskills/`:

```
~/.hackmyskills/
  data.db          # SQLite database (cards, reviews, stats)
  config.toml      # Your configuration
  content/         # User-added YAML question files
  daemon.pid       # Daemon process ID (when running)
  interrupt.bat    # Windows helper for notification clicks
```

### Reset Progress

Delete the database to start fresh:

```bash
rm ~/.hackmyskills/data.db
hms    # Recreates database on next run
```

---

## Development

```bash
# Install with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Validate content
hms validate-content
```

### Project Structure

```
src/hms/
  cli.py              # All CLI commands (Typer)
  quiz.py             # Quiz session engine + question handlers
  gamification.py     # XP, levels, streaks, freezes, mastery
  models.py           # Database models (Peewee ORM)
  loader.py           # YAML content loading
  scheduler.py        # FSRS wrapper
  config.py           # Config reader
  validation.py       # Content validation + duplicate detection
  init.py             # First-run initialization
  content/            # Bundled YAML question banks
  daemon/
    controller.py     # Start/stop/status lifecycle
    scheduler.py      # Notification job + quiet hours
    notifier.py       # Windows desktop notifications (winotify)
    runner.py          # Daemon main loop (APScheduler)
    platform/         # OS-specific startup registration
tests/                # pytest test suite (115 tests)
```

---

## License

MIT
