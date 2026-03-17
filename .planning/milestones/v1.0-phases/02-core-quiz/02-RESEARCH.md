# Phase 2: Core Quiz - Research

**Researched:** 2026-03-15
**Domain:** Terminal quiz session — Rich TUI, single-keypress input, Peewee querying, FSRS rating loop
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Screen handling:** Clear the terminal on each new card — every question gets a clean slate, like a flashcard app. No scroll history during the session.

**Progress indicator:** Progress bar + card count shown at the top of every card screen. Format: `Card 4/10 ──────────── 40%`. Use Rich Progress or a manual Rich Rule + text line.

**Card metadata:** Subtle single-line header above the question in dim text: `[kubernetes · L2]`. Visible but not distracting — topic and difficulty tier always present.

**Flashcard layout:** Question shown in a Rich Panel (blue/cyan border). After reveal, answer shown in a second Rich Panel (green border). Two distinct panels, sequential display — not side-by-side.

**Command-fill layout:** Prompt text in a Panel, then an input line. After submission, show result (correct / incorrect) plus the canonical answer if wrong.

**Scenario layout:** Situation text in a Panel, then A/B/C/D options listed below. Single keypress selects. After selection, show correct answer + explanation.

**Explain-concept layout:** Prompt in a Panel, multiline text input (standard terminal input), then model answer shown in a Panel for self-rating.

**Flashcard reveal:** Any keypress (space or enter) flips the card to show the answer. Simple, fast, no thinking required.

**Self-rating keys:** Number keys 1-4 after reveal: 1=Again (red), 2=Hard (orange), 3=Good (green), 4=Easy (blue). Labels shown on screen so user doesn't need to memorize.

**Command fill-in correctness:** Exact match, case-insensitive — no fuzzy tolerance. Typo is a real miss.

**Scenario answer:** Multiple choice A/B/C/D — single keypress, no enter needed. After selection, immediately show whether correct + brief explanation text.

**Explain-concept:** User types a free-text explanation (standard `input()` line), then model answer shown in green Panel. Self-rating via 1-4 keys, same as flashcard.

**Quit anytime:** Pressing `q` or Ctrl-C ends session cleanly. Cards already reviewed committed to DB. Condensed mini-summary shown.

**Streak credit:** Any review counts — if at least 1 card reviewed today, daily streak is maintained.

**Skip:** No skip option. Rate it 1 (Again) — correct FSRS signal.

**Natural end:** When daily cap is reached (or queue exhausted), show full summary screen.

**Daily cap:** Default 25 cards. Configurable in `~/.hackmyskills/config.toml` under `[quiz] daily_cap = 25`.

**Card order:** Due cards (sorted by `due` ASC) served first. When due queue exhausted, new cards (`due IS NULL`, ordered by topic then ID) fill up to the cap.

**Topic filter:** `hms quiz --topic kubernetes` restricts card selection to `WHERE card.topic = 'kubernetes'`.

**Session summary format:** Full Rich Panel. Contents: cards reviewed, accuracy %, XP earned (bold yellow `+150 XP`), current streak, next session (8 cards due tomorrow). Per-topic breakdown only if >1 topic in session.

**XP display:** Bold highlighted number only — no animation. Phase 2 placeholder: `xp = cards_reviewed * 15`.

**Accuracy definition:** Again (1) and Hard (2) = incorrect. Good (3) and Easy (4) = correct.

**Empty queue message:** "Nothing to review right now — come back tomorrow!" (no summary panel).

**No cards for topic:** Rich error box (red panel): "No cards found for topic 'kubernetes'. Run `hms topics` to see available topics."

**Single-keypress implementation:** Use `readchar` library (cross-platform). `readchar` not yet in pyproject.toml — must be added.

### Claude's Discretion

- How to structure the quiz module (single file `quiz.py` vs. sub-package) — no constraint given
- How to query "cards due today" efficiently — implementation detail
- How to store/compute the streak counter — no DB field specified in CONTEXT.md
- How to compute "8 cards due tomorrow" for summary — implementation detail
- Test structure for the quiz module

### Deferred Ideas (OUT OF SCOPE)

- XP animation / typewriter effect
- "Continue past daily cap" option at summary
- Session replay / review past answers
- Sound effects on correct answer
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| QUIZ-01 | `hms quiz` command starts a focused session | Typer `@app.command()` with `--topic` Option already stubbed in cli.py; replace stub body with session engine call |
| QUIZ-02 | Session serves due cards first, then new cards up to daily cap (default 25) | Peewee queries: `Card.due <= now & due IS NOT NULL` ordered ASC, then `due IS NULL` ordered by topic/id; union result capped at `daily_cap` |
| QUIZ-03 | Daily cap configurable in config.toml | `load_config()["daily_cap"]` already works; `[quiz]` section needs to be documented in default config template |
| QUIZ-04 | Flashcard questions: display prompt, keypress to reveal, self-rating 1-4 | `readchar.readkey()` for flip and rating; Rich Panel blue then green; `scheduler.review_card()` for FSRS update |
| QUIZ-05 | Command fill-in: typed answer, case-insensitive exact match, show correct answer | `input()` for typed answer; `answer.strip().lower() == command.strip().lower()`; no fuzzy — exact only |
| QUIZ-06 | Scenario: situation + A/B/C/D choice, single keypress, show explanation | `readchar.readkey()` after options display; compare to `readchar.key` or raw character; show explanation panel |
| QUIZ-07 | Explain-concept: free-text input, show model answer, self-rate 1-4 | `input()` for explanation; Rich Panel showing model answer; `readchar.readkey()` for 1-4 rating |
| QUIZ-08 | Session summary: cards reviewed, accuracy, XP, streak, next session | Compute from session accumulator; Rich Panel; streak read from DB (ReviewHistory query by today's date); "due tomorrow" Peewee query |
| QUIZ-09 | `hms quiz --topic kubernetes` filters session to that topic | Typer `Option` on quiz command; `WHERE card.topic = topic_filter` appended to both due and new-card queries |
</phase_requirements>

---

## Summary

Phase 2 builds the interactive quiz session engine on top of the Phase 1 foundation. The main challenge is orchestrating four distinct question-type flows (flashcard, command-fill, scenario, explain-concept) through a clean loop that handles single-keypress input, FSRS state updates, and graceful Ctrl-C exits. All the heavy infrastructure — DB, FSRS scheduler, Rich console, Typer CLI — is already in place.

The two new technical elements are: (1) `readchar` library for blocking single-keypress input, which is cross-platform and straightforward; and (2) the card queue query logic that unions due-cards and new-cards with correct ordering and capping. The quiz module itself should be a single `src/hms/quiz.py` file with a clean public entry-point called from `cli.py`.

Streak tracking is the only net-new DB concern: Phase 1 built `ReviewHistory` with `reviewed_at` timestamps, so streak can be computed from that table at summary time without adding a new field.

**Primary recommendation:** Implement `src/hms/quiz.py` as a self-contained session runner; wire the existing `@app.command() def quiz()` stub to call it; add `readchar>=4.0` to pyproject.toml dependencies.

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| readchar | 4.2.1 | Single-keypress input (cross-platform) | Only actively-maintained library for blocking single-char stdin on both Windows and Linux; v4 supports Windows natively |
| rich | >=13.0 (already installed) | Terminal rendering — Panel, Rule, console.clear() | Already used in Phase 1; `console.clear()` confirmed in Rich API |
| typer | >=0.12.0 (already installed) | CLI framework; `hms quiz --topic` Option | Already the project CLI framework |
| peewee | >=4.0.1 (already installed) | Card queue queries; ReviewHistory writes | Already the project ORM |
| fsrs | >=6.3.1 (already installed) | FSRS scheduling after each rating | Already wrapped in hms.scheduler |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime (stdlib) | — | Compute "now" for due-card queries, streak calc | Used in queue-build and summary |
| tomllib (stdlib, Python 3.11+) | — | Read daily_cap from config.toml | Already used in hms.config.load_config() |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| readchar | msvcrt.getwch() (Windows only) | readchar is cross-platform; msvcrt works only on Windows — breaks Linux/WSL |
| readchar | keyboard library | keyboard requires root/admin on Linux; readchar does not |
| exact match (QUIZ-05) | Levenshtein / fuzzy | CONTEXT.md locked: exact case-insensitive only — fuzzy was explicitly rejected |

**Installation (new dependency only):**
```bash
pip install readchar
```

Add to `pyproject.toml` dependencies:
```
"readchar>=4.0",
```

---

## Architecture Patterns

### Recommended Module Structure

```
src/hms/
├── cli.py          # wire quiz() stub to quiz.run_session()
├── quiz.py         # NEW — session runner, question type handlers
├── models.py       # Card, ReviewHistory (existing)
├── scheduler.py    # review_card() wrapper (existing)
├── config.py       # load_config() (existing)
├── db.py           # db object (existing)
└── init.py         # ensure_initialized() (existing)
```

No sub-package needed for Phase 2. A single `quiz.py` keeps all session logic in one file, making the flow readable. If the file grows beyond ~300 lines, handlers can be split in Phase 3.

### Pattern 1: Session Entry Point

**What:** `cli.py` delegates to `quiz.run_session()` with parsed arguments.
**When to use:** Keeps CLI layer thin; quiz logic is independently testable.

```python
# src/hms/cli.py — replace stub
@app.command()
def quiz(
    topic: Optional[str] = typer.Option(None, "--topic", "-t", help="Filter by topic"),
) -> None:
    """Start a focused quiz session."""
    from hms.init import ensure_initialized
    from hms import quiz as quiz_module
    ensure_initialized()
    quiz_module.run_session(topic=topic)
```

### Pattern 2: Card Queue Builder

**What:** Build an ordered list of Card ORM objects up to `daily_cap`. Due cards first (ASC), then new cards (topic ASC, id ASC).
**When to use:** Called once at session start; result is iterated during session loop.

```python
# Source: Peewee querying docs — docs.peewee-orm.com/en/latest/peewee/querying.html
from datetime import datetime, timezone
from hms.models import Card

def build_queue(daily_cap: int, topic: Optional[str] = None) -> list[Card]:
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC to match DB storage

    base = Card.select()
    if topic:
        base = base.where(Card.topic == topic)

    due_cards = (
        base.where(Card.due.is_null(False) & (Card.due <= now))
        .order_by(Card.due.asc())
    )
    new_cards = (
        base.where(Card.due.is_null(True))
        .order_by(Card.topic.asc(), Card.id.asc())
    )

    queue = list(due_cards)
    remaining = daily_cap - len(queue)
    if remaining > 0:
        queue.extend(list(new_cards.limit(remaining)))
    return queue[:daily_cap]
```

### Pattern 3: Single-Keypress Input

**What:** Block until user presses one key; return it as a string.
**When to use:** Flashcard reveal, 1-4 rating, A-D scenario choice, any-key-to-continue.

```python
# Source: readchar 4.2.1 — pypi.org/project/readchar/
import readchar

def wait_for_key(valid_keys: set[str] | None = None) -> str:
    """Block until a valid key is pressed. Ctrl-C raises KeyboardInterrupt."""
    while True:
        key = readchar.readkey()
        if valid_keys is None or key in valid_keys:
            return key
```

Note: `readchar.readkey()` already raises `KeyboardInterrupt` on Ctrl-C — no extra handling needed for that exit path.

### Pattern 4: Screen Clear Per Card

**What:** Clear terminal and reprint progress header before each card.
**When to use:** At the top of every card render call.

```python
# Source: Rich Console API — rich.readthedocs.io/en/stable/reference/console.html
from rich.console import Console
from rich.rule import Rule

console = Console()

def render_progress(card_num: int, total: int) -> None:
    console.clear()
    pct = int((card_num / total) * 100)
    bar_fill = "─" * pct // 5  # approximate 20-char bar
    console.print(f"Card {card_num}/{total} {bar_fill} {pct}%", style="dim")
```

### Pattern 5: FSRS Rating + DB Persist

**What:** After user rates, call `scheduler.review_card()`, update Card fields, write ReviewHistory.
**When to use:** After every card rating regardless of question type.

```python
# Source: hms/scheduler.py and hms/models.py (Phase 1 implementation)
from fsrs import Card as FsrsCard, Rating
from hms.scheduler import review_card
from hms.models import Card as DbCard, ReviewHistory
from datetime import datetime, timezone

def persist_rating(db_card: DbCard, rating: Rating) -> None:
    fsrs_card = FsrsCard.from_json(db_card.fsrs_state) if db_card.fsrs_state else FsrsCard()
    updated_fsrs, review_log = review_card(fsrs_card, rating)

    # Strip timezone (UTC-aware → naive) before Peewee storage
    new_due = updated_fsrs.due.replace(tzinfo=None)

    db_card.fsrs_state = updated_fsrs.to_json()
    db_card.due = new_due
    db_card.stability = updated_fsrs.stability
    db_card.difficulty = updated_fsrs.difficulty
    db_card.state = updated_fsrs.state.name
    db_card.reps += 1
    if rating == Rating.Again:
        db_card.lapses += 1
    db_card.save()

    ReviewHistory.create(
        card=db_card,
        rating=rating.value,
        reviewed_at=datetime.now(timezone.utc).replace(tzinfo=None),
        review_log_json=review_log.to_json(),
    )
```

### Pattern 6: Streak Calculation

**What:** Count distinct calendar days with at least one review in ReviewHistory.
**When to use:** Called once at session end to display streak in summary.

```python
# Source: Peewee querying docs — no new dependency
from datetime import date, datetime
from hms.models import ReviewHistory

def compute_streak() -> int:
    """Return current consecutive-day streak from ReviewHistory."""
    rows = (
        ReviewHistory
        .select(ReviewHistory.reviewed_at)
        .order_by(ReviewHistory.reviewed_at.desc())
        .tuples()
    )
    days_seen: set[date] = set()
    for (dt,) in rows:
        if isinstance(dt, str):
            dt = datetime.fromisoformat(dt)
        days_seen.add(dt.date())

    streak = 0
    check = date.today()
    while check in days_seen:
        streak += 1
        check = check.replace(day=check.day - 1)  # naive decrement — use timedelta
    return streak
```

Use `timedelta(days=1)` for correct date arithmetic — the inline comment is a reminder, not production code.

### Pattern 7: Session Accumulator

**What:** Dataclass tracking per-card results for accuracy and per-topic breakdown.
**When to use:** Updated after every `persist_rating()` call; consumed by summary renderer.

```python
from dataclasses import dataclass, field

@dataclass
class SessionResult:
    total: int = 0
    correct: int = 0  # Good(3) or Easy(4)
    topic_stats: dict[str, dict] = field(default_factory=dict)  # topic -> {total, correct}
    ratings: list[int] = field(default_factory=list)

    def record(self, topic: str, rating_value: int) -> None:
        self.total += 1
        is_correct = rating_value >= 3
        if is_correct:
            self.correct += 1
        self.ratings.append(rating_value)
        ts = self.topic_stats.setdefault(topic, {"total": 0, "correct": 0})
        ts["total"] += 1
        if is_correct:
            ts["correct"] += 1

    @property
    def accuracy_pct(self) -> int:
        return round(100 * self.correct / self.total) if self.total else 0

    @property
    def xp(self) -> int:
        return self.total * 15  # Phase 2 placeholder; Phase 3 replaces this
```

### Anti-Patterns to Avoid

- **Importing `console` from cli.py in quiz.py**: Creates circular imports. Define `console = Console()` at module level in `quiz.py` independently, or pass it as argument.
- **Calling `db.create_tables()` in quiz.py**: Tables are created by `ensure_initialized()` in `cli.py` before `quiz_module.run_session()` is called. Never duplicate table creation.
- **Using `input()` for single-keypress paths**: `input()` requires Enter. Only use `input()` for command-fill typed answers and explain-concept free-text — all rating/reveal/choice inputs must use `readchar.readkey()`.
- **Storing UTC-aware datetimes in Peewee DateTimeField**: Always call `.replace(tzinfo=None)` on `fsrs.Card.due` before saving — established Phase 1 pattern.
- **Building the card queue inside the session loop**: Build once at session start and iterate. Re-querying inside the loop can lead to inconsistent counts if new reviews change due dates.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| FSRS scheduling math | Custom spaced-repetition algorithm | `fsrs.Scheduler` via `hms.scheduler.review_card()` | FSRS-6 has 21 tuned parameters; hand-rolled SM-2 variants diverge in accuracy |
| Single-keypress stdin | `msvcrt.getwch()` + Unix `termios` conditional | `readchar.readkey()` | readchar handles Windows vs Unix branching internally; no platform conditionals needed |
| Streak calculation | External streak table | Derive from `ReviewHistory.reviewed_at` | ReviewHistory is already written per rating; a redundant streak table adds sync bugs |
| Terminal width detection | `os.get_terminal_size()` manually | `rich.Console` (handles it automatically) | Rich Console reads terminal width for panel sizing; no manual detection needed |

---

## Common Pitfalls

### Pitfall 1: `readchar.readkey()` Inside `typer.testing.CliRunner`

**What goes wrong:** `CliRunner` captures stdin/stdout via a pipe; `readchar.readkey()` reads directly from the OS terminal, not from the piped stdin. Tests that invoke quiz via CliRunner will hang waiting for a real keypress.

**Why it happens:** `readchar` bypasses Python's `sys.stdin` and reads from the OS-level terminal device.

**How to avoid:** Inject a keypress callable via dependency injection (default: `readchar.readkey`; test override: a mock that returns predefined keys). Example:

```python
def run_session(topic=None, _readkey=None):
    if _readkey is None:
        import readchar
        _readkey = readchar.readkey
    ...
```

**Warning signs:** Test hangs indefinitely on `hms quiz` invocation.

### Pitfall 2: UTC-naive/aware Mismatch in Due-Card Query

**What goes wrong:** `datetime.now()` (naive) compared to a stored naive UTC value may return wrong results if the code is accidentally changed to `datetime.now(timezone.utc)` (aware).

**Why it happens:** Phase 1 decision: naive UTC stored in Peewee. Comparing an aware datetime to a naive-stored column produces a `TypeError` in Python or silently wrong results.

**How to avoid:** Always use `datetime.now(timezone.utc).replace(tzinfo=None)` as the "now" reference in due-card queries. Add a comment: `# naive UTC — matches DB storage`.

**Warning signs:** `TypeError: can't compare offset-naive and offset-aware datetimes` in test output.

### Pitfall 3: Empty Queue vs. No Cards for Topic

**What goes wrong:** Showing "Nothing to review" when the user's `--topic` argument has a typo (e.g., `Kubernetes` vs `kubernetes`) — but there are cards, just no matching ones.

**Why it happens:** Both empty-queue and no-topic-cards return zero results from `build_queue()`. The distinction requires a separate check.

**How to avoid:** Before building the session queue, run a separate count query: `Card.select().where(Card.topic == topic_filter).count()`. If zero: show red "No cards found for topic" error. If non-zero but queue is empty: show "Nothing to review right now."

**Warning signs:** User gets "Nothing to review" when they clearly imported cards for that topic.

### Pitfall 4: config.toml `daily_cap` Nesting

**What goes wrong:** `load_config()` uses `config.update(user_config)` which shallow-merges. If the user writes `[quiz]\ndaily_cap = 50` in TOML, it will be stored as `{"quiz": {"daily_cap": 50}}`, but the current DEFAULT_CONFIG has `"daily_cap": 25` at the top level.

**Why it happens:** CONTEXT.md specifies `[quiz] daily_cap = 25` as the TOML path, but the existing `config.py` DEFAULT_CONFIG has `"daily_cap"` at the root level.

**How to avoid:** Either (a) read `config.get("quiz", {}).get("daily_cap", 25)` with the nested TOML structure, or (b) keep `daily_cap` at TOML root (no `[quiz]` section). Pick one and document in the default config template. Recommend option (b) — keep flat — since DEFAULT_CONFIG is already flat and the planner should document it clearly.

**Warning signs:** `daily_cap` always reads as 25 even when user sets it in TOML.

### Pitfall 5: Ctrl-C Mid-Rating vs. Mid-Render

**What goes wrong:** If `KeyboardInterrupt` is raised inside `persist_rating()` (after FSRS computed but before `ReviewHistory.create()`), the card state is inconsistent — updated in `Card` table but no `ReviewHistory` row.

**Why it happens:** `readchar.readkey()` propagates Ctrl-C as `KeyboardInterrupt`; if the interrupt fires at the wrong moment, the DB is partially written.

**How to avoid:** Wrap `persist_rating()` in a try/except that catches `KeyboardInterrupt` and re-raises only after the DB transaction completes. Or use Peewee's `db.atomic()` context to make the card update + history write atomic:

```python
with db.atomic():
    db_card.save()
    ReviewHistory.create(...)
```

**Warning signs:** Cards show updated FSRS state but no review history rows.

---

## Code Examples

Verified patterns from official sources:

### Rich Panel with border_style
```python
# Source: Rich docs — rich.readthedocs.io/en/stable/panel.html
from rich.panel import Panel
from rich.console import Console

console = Console()
console.print(Panel("Question text here", border_style="blue", title="[dim]kubernetes · L2[/dim]"))
console.print(Panel("Answer text here", border_style="green"))
```

### Rich console.clear()
```python
# Source: Rich Console API — rich.readthedocs.io/en/stable/reference/console.html
console.clear()  # signature: clear(home: bool = True)
# Clears screen and moves cursor to home position
```

### Peewee due-card query (verified pattern)
```python
# Source: Peewee querying docs — docs.peewee-orm.com/en/latest/peewee/querying.html
from datetime import datetime, timezone
now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

due_cards = (
    Card.select()
    .where(Card.due.is_null(False) & (Card.due <= now))
    .order_by(Card.due.asc())
)
new_cards = (
    Card.select()
    .where(Card.due.is_null(True))
    .order_by(Card.topic.asc(), Card.id.asc())
)
```

### readchar single keypress (verified)
```python
# Source: readchar 4.2.1 PyPI — pypi.org/project/readchar/
import readchar

key = readchar.readkey()  # blocks; returns str; Ctrl-C raises KeyboardInterrupt
# For single chars: readchar.readchar() — length-1 string
# For special keys: compare to readchar.key.ENTER, readchar.key.SPACE, etc.
```

### Peewee atomic transaction
```python
# Source: Peewee docs — docs.peewee-orm.com
from hms.db import db

with db.atomic():
    db_card.save()
    ReviewHistory.create(card=db_card, rating=rating.value, ...)
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| curses for terminal TUI | Rich library | ~2020 | No need for curses; Rich handles styling, panels, clearing |
| msvcrt (Windows) + termios (Unix) conditionals | `readchar` library | Ongoing — readchar 4.x | Single cross-platform import |
| FSRS v4 (17 params) | FSRS v6 (21 params) | 2024 | Already using v6 via `fsrs>=6.3.1` |

**Deprecated/outdated:**
- `curses` for simple terminal quiz apps: Rich is simpler and doesn't require the curses terminal mode overhead for this use case.
- Manual `os.system("cls")` / `os.system("clear")`: use `console.clear()` instead — Rich handles platform differences.

---

## Open Questions

1. **`daily_cap` TOML nesting**
   - What we know: CONTEXT.md says `[quiz] daily_cap = 25` (nested), but `config.py` DEFAULT_CONFIG is flat (`"daily_cap": 25`).
   - What's unclear: Which structure to use — flat root key or `[quiz]` section.
   - Recommendation: Planner should choose flat (matches existing code) and document that `daily_cap = 25` is a root-level key in config.toml, not nested under `[quiz]`.

2. **"Due tomorrow" count in summary**
   - What we know: Summary shows "8 cards due tomorrow".
   - What's unclear: Efficient computation — query all cards with `due` between start-of-tomorrow and end-of-tomorrow (naive UTC).
   - Recommendation: `Card.select().where(Card.due.between(tomorrow_start, tomorrow_end)).count()` — straightforward Peewee query.

3. **Streak DB field vs. computed**
   - What we know: `ReviewHistory` has `reviewed_at` timestamps; no dedicated streak table exists.
   - What's unclear: Whether computing streak by scanning ReviewHistory rows is performant enough at scale.
   - Recommendation: Compute from ReviewHistory for Phase 2. At Phase 2 scale (<1000 review rows) this is instant. A dedicated streak field in a GameState model is a Phase 3 concern.

---

## Validation Architecture

`workflow.nyquist_validation` is `true` in `.planning/config.json` — validation section is required.

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.x |
| Config file | `pyproject.toml` — `[tool.pytest.ini_options]` (`testpaths = ["tests"]`, `addopts = "-x -q"`) |
| Quick run command | `pytest tests/test_quiz.py -x -q` |
| Full suite command | `pytest -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| QUIZ-01 | `hms quiz` command starts session (no-op for empty queue) | unit | `pytest tests/test_quiz.py::test_quiz_empty_queue -x -q` | Wave 0 |
| QUIZ-02 | Due cards served before new cards; capped at daily_cap | unit | `pytest tests/test_quiz.py::test_build_queue_order -x -q` | Wave 0 |
| QUIZ-03 | daily_cap read from config.toml overrides default | unit | `pytest tests/test_quiz.py::test_daily_cap_from_config -x -q` | Wave 0 |
| QUIZ-04 | Flashcard flow: keypress reveals answer, rating persists FSRS state | unit (mock readkey) | `pytest tests/test_quiz.py::test_flashcard_flow -x -q` | Wave 0 |
| QUIZ-05 | Command-fill: case-insensitive exact match, correct/incorrect result | unit | `pytest tests/test_quiz.py::test_command_fill_correct` + `test_command_fill_incorrect -x -q` | Wave 0 |
| QUIZ-06 | Scenario: A/B/C/D keypress selects, explanation shown | unit (mock readkey) | `pytest tests/test_quiz.py::test_scenario_flow -x -q` | Wave 0 |
| QUIZ-07 | Explain-concept: free input shown, model answer displayed, 1-4 rating persists | unit (mock readkey + input) | `pytest tests/test_quiz.py::test_explain_concept_flow -x -q` | Wave 0 |
| QUIZ-08 | Session accumulator: accuracy %, XP, streak computed correctly | unit | `pytest tests/test_quiz.py::test_session_result_accuracy -x -q` | Wave 0 |
| QUIZ-09 | `--topic` filter applies to both due and new card queries | unit | `pytest tests/test_quiz.py::test_build_queue_topic_filter -x -q` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_quiz.py -x -q`
- **Per wave merge:** `pytest -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_quiz.py` — all QUIZ-01 through QUIZ-09 test stubs
- [ ] `readchar>=4.0` added to `pyproject.toml` dependencies (required before quiz.py can import it)
- [ ] `src/hms/quiz.py` — module must exist for test imports to resolve

*(conftest.py and pytest config already exist from Phase 1 — no gaps there)*

---

## Sources

### Primary (HIGH confidence)
- readchar 4.2.1 PyPI page (pypi.org/project/readchar/) — version, API, platform support
- readchar GitHub (github.com/magmax/python-readchar) — Ctrl-C behavior, Windows support details
- Rich Console API reference (rich.readthedocs.io/en/stable/reference/console.html) — `console.clear(home=True)` confirmed
- Peewee querying docs (docs.peewee-orm.com/en/latest/peewee/querying.html) — `is_null()`, `order_by()`, `db.atomic()`
- Phase 1 source code in `src/hms/` — confirmed DB schema, FSRS integration patterns, naive UTC convention

### Secondary (MEDIUM confidence)
- Rich Panel and Rule usage patterns — confirmed via Rich readthedocs.io navigation + Phase 1 existing code
- Peewee query operator docs (docs.peewee-orm.com/en/latest/peewee/query_operators.html) — `is_null()` syntax

### Tertiary (LOW confidence)
- None — all critical claims verified from primary sources.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — readchar 4.2.1 confirmed on PyPI; all other deps confirmed in pyproject.toml and working in Phase 1
- Architecture: HIGH — patterns derived from existing Phase 1 code and verified library APIs
- Pitfalls: HIGH — Pitfall 1 (readchar/CliRunner) is a known pattern in CLI testing; Pitfalls 2-5 derived from Phase 1 decisions and DB schema
- Validation architecture: HIGH — pytest config confirmed in pyproject.toml; test commands follow existing pattern

**Research date:** 2026-03-15
**Valid until:** 2026-04-15 (stable libraries; readchar and Rich have infrequent breaking changes)
