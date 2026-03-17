# Phase 3: Gamification + Adaptive Difficulty - Research

**Researched:** 2026-03-15
**Domain:** Python CLI gamification mechanics, SQLite-backed adaptive unlock logic, Rich terminal display
**Confidence:** HIGH

## Summary

Phase 3 is a pure in-process implementation phase with no new external dependencies. Every technical building block is already present: Peewee ORM for SQLite queries, Rich for display, and `Card.state`/`ReviewHistory` tables that store exactly the data needed for XP, streaks, and mastery calculations. The architecture is an augmentation of existing code rather than greenfield work.

The three plan areas (XP+streak+level system, adaptive unlock + tier-aware queue, `hms stats` display) each operate on a well-defined data surface. The key risk is the interaction between streak freeze logic and the existing `compute_streak()` function, which currently has no concept of freezes. This function must be extended — not replaced — to maintain backward compatibility with the existing summary display.

The adaptive unlock logic is the highest-complexity calculation: per-topic mastery ratios drive which tiers are queryable in `build_queue`. Card selection in Phase 2's `build_queue` is currently tier-unaware and must be extended to filter out locked tiers.

**Primary recommendation:** Build a thin `gamification.py` module that owns XP, streak, freeze, level, and mastery queries — keeping `quiz.py` and `cli.py` as callers. This avoids bloating either existing module and keeps all gamification state in one place for Phase 4/5 to extend.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**XP Formula**
- Base XP by tier: L1 = 5 XP, L2 = 10 XP, L3 = 20 XP per card
- Recall quality multiplier: Again = 0×, Hard = 0.5×, Good = 1.0×, Easy = 1.5×
  - Again earns zero XP — you didn't know it; Hard earns half; Easy gets a bonus
- Streak multiplier: +10% XP per 7-day streak milestone, capped at +50% (applies at day 7, 14, 21, 28, 35+)
  - Applied to the subtotal after tier × rating, rounded to nearest integer
- Formula: `xp = round(base_tier_xp * rating_multiplier * streak_multiplier)`
- Replaces Phase 2 placeholder: `xp = cards_reviewed * 15` is replaced in `SessionResult.xp`

**Streak & Freeze System**
- Daily streak: Increments when ≥1 card is reviewed on a calendar day (local date)
- Missed day: If no review happened yesterday, streak resets to 0 — unless a freeze is consumed
- Streak freeze: Earned every 7 consecutive days; stored as an integer count; consumed automatically on first missed day (not a choice)
- Freeze display: Show count in stats as "Freezes: N" — if 0, omit from dashboard to avoid noise
- Streak check timing: Evaluated at the start of each `hms quiz` session and on `hms stats`

**Level System**
- 10 levels, DevOps-themed names (fixed order):
  1. Pipeline Rookie
  2. Container Cadet
  3. YAML Wrangler
  4. CI Operator
  5. Cloud Apprentice
  6. Terraform Tinkerer
  7. Cluster Admin
  8. SRE Initiate
  9. Container Captain
  10. DevOps Architect
- Linear XP progression: 500 XP per level; 5,000 XP total to reach max
- Level is derived at display time from total XP — no separate `level` field needed in DB
- At max level (DevOps Architect): Show "Max Level" instead of XP progress bar

**Adaptive Difficulty — Mastery & Unlocking**
- Mastery definition: A card is mastered when its FSRS `state` field = `"Review"` (promoted out of Learning/Relearning). Stored in `Card.state` (CharField, already in the model).
- Unlock threshold: A tier unlocks for a topic when ≥80% of that topic's cards at the current tier are mastered (state = Review)
  - L2 unlocks per-topic: mastered ≥80% of topic's L1 cards
  - L3 unlocks per-topic: mastered ≥80% of topic's L2 cards
- Mastery % calculation: `mastered_count / total_count` where total = all cards for that topic+tier in DB
- Unlock notification: If a tier just unlocked for any topic during the session, show a highlighted line at the end of the session summary panel
  - `🔓 L2 kubernetes unlocked! Harder cards are now available.`
  - Check for new unlocks by comparing unlock status before vs. after session
- Card selection in hms quiz (no --topic): Serve due cards from all unlocked tiers for all topics. Do not serve L2 cards for a topic if L2 is still locked. Within the due queue, no special tier ordering — FSRS `due` ASC governs.

**hms stats Display**
- Structure: Single Rich Panel titled "HackMySkills Stats"
- Top section (summary):
  - Streak: `🔥 5 days` (or `5 day streak` if emoji unreliable) + Freezes: N (omit if 0)
  - Level name + number: `Level 3 · YAML Wrangler`
  - XP progress bar: `XP: 1240 / 1500  [████████░░] 83%` — use Rich Progress or a manual bar
  - Cards due today: `18 cards due`
- Per-topic table (bottom of panel): Rich Table with columns: `Topic | Due | Mastery% | Tier`
  - Mastery% = (state=Review cards) / (total cards for topic) as integer percent
  - Tier = highest tier currently unlocked for that topic (L1/L2/L3)
  - Sort: by Due DESC (most urgent first)
- No-args dashboard update: `hms` with no args should now show:
  - Streak + level name (motivating one-liner)
  - Cards due today
  - "Run hms quiz to start" prompt
  - Replaces the Phase 1 placeholder dashboard

### Claude's Discretion
- Exact XP bar character style (block chars vs. Rich's built-in bar)
- Whether to show a level-up message mid-session or only in summary
- How to handle edge case: topic has 0 cards in a tier (treat as unlocked? skip tier?)
- Error display if DB has no review history yet (first-run stats)

### Deferred Ideas (OUT OF SCOPE)
- XP animation / level-up fanfare — Rich doesn't animate well in static mode
- Badges/achievements (GAME-V2-01) — v2 requirement, not Phase 3
- Weekly/monthly summary report (GAME-V2-02) — v2 requirement
- FSRS optimizer to personalize weights (GAME-V2-03) — v2 requirement
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| GAME-01 | XP awarded per review — formula tied to recall quality and card difficulty tier | XP formula fully specified; `SessionResult.ratings` + `Card.tier` already available per review; requires per-card XP accumulation instead of session-level `total * 15` |
| GAME-02 | Daily streak tracked — increments when at least 1 card reviewed per calendar day | `compute_streak()` exists; must add freeze awareness; `ReviewHistory.reviewed_at` stores naive UTC datetimes — convert to local date for calendar-day logic |
| GAME-03 | Streak freeze earned every 7 days — protects streak on one missed day | Freeze count needs storage; lightest approach is a new `UserStat` table or a single-row table; freeze auto-consumed on missed day detection in streak check |
| GAME-04 | Level system based on total XP with visible level name | Level derived from total XP at display time; total XP = sum over all ReviewHistory of computed XP-per-review; requires per-review XP to be queryable |
| GAME-05 | `hms stats` shows streak, freezes, level, XP to next level, cards due, performance by topic | `stats()` command in cli.py exists as stub; needs full implementation via gamification module queries |
| ADAPT-01 | Cards tagged L1/L2/L3 — difficulty tier shown during session | Already implemented: `card.tier` displayed as `[dim][topic · tier][/dim]` in every handler |
| ADAPT-02 | New cards start at L1; unlock L2 for a topic after mastering ≥80% of L1 cards | Mastery check: `Card.select().where(Card.topic==t, Card.tier=='L1', Card.state=='Review').count()` / total L1; `build_queue` must filter out locked tiers |
| ADAPT-03 | L3 cards unlock after mastering ≥80% of L2 cards in a topic | Same mastery pattern as ADAPT-02 but for L2→L3 transition |
| ADAPT-04 | `hms quiz` defaults to serving mixed tiers based on unlock status — not just easy cards | `build_queue()` must be extended to accept unlock status and filter `Card.tier` accordingly |
</phase_requirements>

---

## Standard Stack

### Core (already installed — no new dependencies needed)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| peewee | 4.0 | ORM for SQLite queries | Already in use; mastery queries are simple COUNT aggregates |
| rich | (current) | Terminal display — Panel, Table, Progress | Already in use; `console = Console()` established per-module |
| typer | (current) | CLI command registration | `@app.command()` pattern established in cli.py |

### Supporting (already installed)
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| datetime | stdlib | Date arithmetic for streak calculation | Local date comparison for calendar-day logic |
| math | stdlib | `round()` for XP formula | Already a builtin; no import needed |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Manual XP bar with block chars | Rich `Progress` widget | Progress widget is designed for live updating tasks; static bar with block chars is simpler and matches the non-animated constraint |
| Per-review XP in ReviewHistory | Recompute XP from ratings on each stats call | Recompute is cleaner (no migration) and feasible since total reviews are bounded by daily cap × days; prefer recompute to avoid schema change |

**Installation:** No new packages required for Phase 3.

## Architecture Patterns

### Recommended Module Structure
```
src/hms/
├── gamification.py    # NEW — XP, streak, freeze, level, mastery, unlock logic
├── quiz.py            # MODIFY — replace SessionResult.xp, extend build_queue, add unlock notification
├── cli.py             # MODIFY — update _show_dashboard(), implement stats()
└── models.py          # MODIFY — add UserStat table (freeze storage)
```

### Pattern 1: Thin Gamification Module
**What:** A single `gamification.py` that owns all gamification state queries. `quiz.py` and `cli.py` import from it.
**When to use:** Any time gamification data is needed in a display or session context.
**Example:**
```python
# src/hms/gamification.py

from datetime import date, timedelta
from hms.models import Card, ReviewHistory, UserStat

LEVEL_NAMES = [
    "Pipeline Rookie",
    "Container Cadet",
    "YAML Wrangler",
    "CI Operator",
    "Cloud Apprentice",
    "Terraform Tinkerer",
    "Cluster Admin",
    "SRE Initiate",
    "Container Captain",
    "DevOps Architect",
]
XP_PER_LEVEL = 500
TIER_BASE_XP = {"L1": 5, "L2": 10, "L3": 20}
RATING_MULTIPLIER = {1: 0.0, 2: 0.5, 3: 1.0, 4: 1.5}  # Again/Hard/Good/Easy
MASTERY_THRESHOLD = 0.80
UNLOCK_TIERS = {"L1": None, "L2": "L1", "L3": "L2"}  # tier -> prerequisite tier

def compute_xp_for_review(tier: str, rating_value: int, streak: int) -> int:
    base = TIER_BASE_XP.get(tier, 5)
    multiplier = RATING_MULTIPLIER.get(rating_value, 0.0)
    milestones = min(streak // 7, 5)  # cap at +50% (5 milestones * 10%)
    streak_multiplier = 1.0 + milestones * 0.10
    return round(base * multiplier * streak_multiplier)

def get_total_xp() -> int:
    """Sum XP across all ReviewHistory rows by recomputing per-review XP."""
    ...

def get_level_info(total_xp: int) -> dict:
    """Return level number (1-10), name, xp_in_level, xp_for_next."""
    ...

def is_tier_unlocked(topic: str, tier: str) -> bool:
    """Return True if tier is unlocked for topic."""
    if tier == "L1":
        return True  # L1 always unlocked
    prereq = UNLOCK_TIERS[tier]
    total = Card.select().where(Card.topic == topic, Card.tier == prereq).count()
    if total == 0:
        return True  # edge case: no prereq cards => treat as unlocked
    mastered = Card.select().where(
        Card.topic == topic,
        Card.tier == prereq,
        Card.state == "Review"
    ).count()
    return (mastered / total) >= MASTERY_THRESHOLD

def get_unlocked_tiers_per_topic() -> dict[str, list[str]]:
    """Return {topic: [unlocked_tiers]} for all topics."""
    ...
```

### Pattern 2: Freeze Storage via UserStat Single-Row Table
**What:** A new `UserStat` model with a single row (get_or_create with id=1) storing freeze count and last-freeze-awarded day.
**When to use:** Freeze count must persist across sessions; it's the only new persistent state needed.
**Example:**
```python
# src/hms/models.py addition

class UserStat(BaseModel):
    """Single-row table for user-level persistent gamification state."""
    streak_freezes = IntegerField(default=0)
    last_freeze_awarded_day = CharField(default="")  # ISO date "YYYY-MM-DD" or ""

    class Meta:
        table_name = "userstat"

# Access pattern:
stat, _ = UserStat.get_or_create(id=1)
```

### Pattern 3: Streak + Freeze Check at Session Start
**What:** At the start of `hms quiz` and `hms stats`, run a streak+freeze check that may consume a freeze or reset the streak.
**When to use:** Before building the queue or displaying stats.
**Example:**
```python
def update_streak_with_freeze(stat: UserStat) -> int:
    """Evaluate streak state, consuming a freeze if yesterday was missed.

    Returns current streak count after any freeze consumption.
    Side effect: saves UserStat if a freeze was consumed.
    """
    today = date.today()
    yesterday = today - timedelta(days=1)
    rows = list(ReviewHistory.select().order_by(ReviewHistory.reviewed_at.desc()))
    review_dates = {row.reviewed_at.date() for row in rows}

    # Check if yesterday was missed
    if yesterday not in review_dates and today not in review_dates:
        # Missed yesterday AND haven't reviewed today yet
        if stat.streak_freezes > 0:
            stat.streak_freezes -= 1
            stat.save()
            # Insert sentinel review for yesterday to preserve streak count?
            # No — instead, compute streak normally; freeze means we don't reset
        # else: streak resets naturally (no freeze available)
    ...
```

**Note on freeze sentinel approach:** The freeze does NOT insert a fake ReviewHistory row. Instead, `compute_streak()` must be made freeze-aware: when walking back days, if a day is missed and a freeze was active for that day, it continues the streak. This requires storing which day the freeze was used (or checking `last_freeze_used_day` on UserStat).

### Pattern 4: Tier-Aware build_queue Extension
**What:** `build_queue()` gains an optional `unlocked_tiers` parameter (dict[topic, list[str]] or None). When provided, cards for a topic+tier not in the unlocked set are excluded.
**When to use:** Called from `run_session()` for no-topic sessions; topic-filtered sessions already skip the question entirely.
**Example:**
```python
def build_queue(
    daily_cap: int,
    topic: Optional[str] = None,
    unlocked_tiers: Optional[dict[str, list[str]]] = None,
) -> list[Card]:
    ...
    base_due = Card.select()
    if unlocked_tiers is not None:
        # Build a WHERE clause: (topic='k8s' AND tier IN ('L1')) OR (topic='tf' AND tier IN ('L1','L2')) ...
        from peewee import ModelSelect
        conditions = []
        for t, tiers in unlocked_tiers.items():
            conditions.append((Card.topic == t) & (Card.tier.in_(tiers)))
        if conditions:
            from functools import reduce
            import operator
            base_due = base_due.where(reduce(operator.or_, conditions))
    ...
```

### Anti-Patterns to Avoid
- **Storing total XP in DB:** Recompute from ReviewHistory on each stats call. Avoids migration complexity and keeps XP formula changes retroactive.
- **Modifying ReviewHistory schema:** Do not add an `xp` column. Per-review XP is deterministic from (tier, rating, streak_at_time). Computing streak_at_time historically is complex — instead, compute current total XP by summing `compute_xp_for_review(tier, rating, current_streak)` for all history rows. (Note: this means historical XP reflects today's streak multiplier, which is acceptable — the UX is motivational, not an audit trail.)
- **Circular imports between quiz.py and gamification.py:** quiz.py imports gamification; gamification imports only models and stdlib. Do not import quiz from gamification.
- **Using Rich `Live` or `Progress` with `transient=False` for XP bar:** Use a manual progress bar string with block characters (`█░`) for the XP display — it's static, already printed, matches the no-animation constraint.
- **Checking unlock status inside every handler:** Unlock status is checked once per session (before and after), not per-card. Keep handlers lightweight.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Mastery % query | Custom SQL string with f-strings | Peewee `.where()` + `.count()` with indexed fields | SQL injection risk, Peewee already handles this cleanly |
| XP progress bar rendering | Custom terminal escape codes | Manual string with `█` / `░` block characters (Unicode U+2588, U+2591) | No ANSI escape needed; Rich handles the console write |
| Level derivation | Lookup table stored in DB | Pure function from `total_xp // XP_PER_LEVEL` | Derived value — no DB storage needed |
| Streak computation | Storing streak in DB field | Walk backward from today over `ReviewHistory.reviewed_at` dates | DB-stored streak can desync; recompute is cheap since daily cap is small |

**Key insight:** All gamification state is derivable from the two existing tables (Card + ReviewHistory) plus one new single-row table (UserStat for freeze count). No migrations to existing tables are needed.

## Common Pitfalls

### Pitfall 1: Naive UTC vs. Local Date in Streak Calculation
**What goes wrong:** `ReviewHistory.reviewed_at` is stored as naive UTC. A review at 22:00 local time on Monday may be stored as 03:00 Tuesday UTC — making the streak calculation miss "Monday" when using `.date()` directly.
**Why it happens:** The existing `compute_streak()` calls `.reviewed_at.date()` on naive UTC datetimes. For users in UTC+X timezones, late-evening reviews may fall on the next UTC day.
**How to avoid:** Use `datetime.now().date()` (local) for `date.today()` comparison, and convert `reviewed_at` to local time before extracting `.date()`. Since this is a solo local tool, `datetime.fromtimestamp(reviewed_at.timestamp()).date()` is not applicable for naive datetimes — use `reviewed_at.date()` as-is and accept UTC-day semantics, OR store reviewed_at in local time. The CONTEXT.md says "local date" — existing code stores naive UTC — this mismatch must be consciously chosen or worked around.
**Warning signs:** Tests pass in UTC but user reports streak resetting at midnight UTC rather than local midnight.
**Recommendation:** For Phase 3, document the UTC-day convention (consistent with existing Phase 2 behavior) and note it as a known limitation. Don't change the storage format mid-phase.

### Pitfall 2: Freeze Logic Complexity with Existing compute_streak()
**What goes wrong:** The existing `compute_streak()` walks back days from today. Inserting a freeze-consumed sentinel row in ReviewHistory would pollute review data. Not inserting it means the streak walk sees a gap and stops.
**Why it happens:** The freeze must bridge a missing day without creating fake review rows.
**How to avoid:** Replace `compute_streak()` with a freeze-aware version that, when walking back, checks UserStat.last_freeze_used_day — if the missing day equals that date, it skips the gap once and continues counting.
**Warning signs:** Streak resets even after a freeze was available; freeze count decrements but streak still shows 0.

### Pitfall 3: build_queue Returning Locked Cards
**What goes wrong:** Without tier filtering, `hms quiz` with no `--topic` will serve L2/L3 cards for topics where those tiers are locked — contradicting ADAPT-04.
**Why it happens:** Phase 2's `build_queue` has no unlock awareness.
**How to avoid:** Always call `get_unlocked_tiers_per_topic()` before `build_queue()` in `run_session()` when no `--topic` is given. Pass unlock status into `build_queue`. For `--topic` sessions, topic-specific unlock status still applies.
**Warning signs:** L2 cards appear before the 80% L1 mastery threshold is crossed.

### Pitfall 4: Edge Case — Topic Has Zero Cards in Prerequisite Tier
**What goes wrong:** `mastered / total` raises ZeroDivisionError if `total == 0`.
**Why it happens:** A topic may have only L2/L3 cards loaded, or content is partially loaded.
**How to avoid:** In `is_tier_unlocked()`, check `if total == 0: return True` — a tier with no prerequisite cards is treated as unlocked. Document this behavior as a known design choice (per Claude's Discretion in CONTEXT.md).

### Pitfall 5: XP Formula Applied at Session Level vs. Per-Card
**What goes wrong:** Phase 2's `SessionResult.xp` computes `total * 15` — a session aggregate. Phase 3's formula requires per-card data (tier + rating) and the streak at the time the session started.
**Why it happens:** `SessionResult` only tracks `ratings` as a flat list — it does not track tier per rating.
**How to avoid:** Either (a) change `SessionResult.record()` to also capture `tier` per card, or (b) accumulate XP incrementally in `record()`. Option (a) is cleaner — add `tier` to the record call and store `[(tier, rating_value), ...]` in `cards_reviewed`. Then `session.xp` iterates the list.

### Pitfall 6: Unlock Notification Diff Requires Pre-Session Snapshot
**What goes wrong:** If unlock status is only computed after a session, there's no way to know which tiers newly unlocked during the session.
**Why it happens:** Without a "before" snapshot, the "after" snapshot is the only state.
**How to avoid:** In `run_session()`, snapshot `get_unlocked_tiers_per_topic()` before the session loop. After the loop, snapshot again. The diff is new unlocks to announce.

## Code Examples

### XP Formula Implementation
```python
# Source: gamification.py (new module — no external source)
TIER_BASE_XP = {"L1": 5, "L2": 10, "L3": 20}
RATING_MULTIPLIER = {1: 0.0, 2: 0.5, 3: 1.0, 4: 1.5}

def compute_xp_for_review(tier: str, rating_value: int, streak: int) -> int:
    base = TIER_BASE_XP.get(tier, 5)
    multiplier = RATING_MULTIPLIER.get(rating_value, 0.0)
    milestones = min(streak // 7, 5)
    streak_multiplier = 1.0 + milestones * 0.10
    return round(base * multiplier * streak_multiplier)
```

### Level Derivation
```python
# Source: gamification.py
XP_PER_LEVEL = 500
MAX_LEVEL = 10

def get_level_info(total_xp: int) -> dict:
    level = min(total_xp // XP_PER_LEVEL + 1, MAX_LEVEL)
    if level >= MAX_LEVEL:
        return {"level": MAX_LEVEL, "name": LEVEL_NAMES[-1], "is_max": True, "xp_to_next": 0}
    xp_in_level = total_xp % XP_PER_LEVEL
    xp_to_next = XP_PER_LEVEL - xp_in_level
    return {
        "level": level,
        "name": LEVEL_NAMES[level - 1],
        "is_max": False,
        "xp_in_level": xp_in_level,
        "xp_to_next": xp_to_next,
        "xp_for_level": XP_PER_LEVEL,
    }
```

### Mastery Query (Peewee)
```python
# Source: gamification.py
def mastery_ratio(topic: str, tier: str) -> float:
    total = Card.select().where(Card.topic == topic, Card.tier == tier).count()
    if total == 0:
        return 1.0  # treat empty tier as mastered (unlocks next tier)
    mastered = Card.select().where(
        Card.topic == topic,
        Card.tier == tier,
        Card.state == "Review"
    ).count()
    return mastered / total
```

### Static XP Progress Bar
```python
# Source: gamification.py — manual block character bar (no Rich Progress widget)
def format_xp_bar(xp_in_level: int, xp_for_level: int, width: int = 10) -> str:
    pct = xp_in_level / xp_for_level if xp_for_level else 0
    filled = round(pct * width)
    bar = "█" * filled + "░" * (width - filled)
    pct_int = round(pct * 100)
    return f"[{bar}] {pct_int}%"
```

### Rich Stats Panel (structure)
```python
# Source: cli.py — stats() command
from rich.table import Table

def _render_stats_panel() -> None:
    from hms.gamification import (
        get_total_xp, get_level_info, compute_streak_with_freeze,
        get_unlocked_tiers_per_topic, mastery_ratio
    )
    from hms.models import Card
    from datetime import datetime, timezone

    total_xp = get_total_xp()
    level_info = get_level_info(total_xp)
    streak, freezes = compute_streak_with_freeze()

    now = datetime.now(timezone.utc).replace(tzinfo=None)
    due_today = Card.select().where(Card.due <= now).count()

    # Build per-topic table
    topics = [c.topic for c in Card.select(Card.topic).distinct()]
    table = Table(show_header=True, header_style="bold")
    table.add_column("Topic")
    table.add_column("Due", justify="right")
    table.add_column("Mastery%", justify="right")
    table.add_column("Tier")
    ...
```

### UserStat Model Addition
```python
# src/hms/models.py — addition
from peewee import BooleanField  # not needed; IntegerField and CharField suffice

class UserStat(BaseModel):
    """Single-row table for persistent gamification state (id=1 always)."""
    streak_freezes = IntegerField(default=0)
    last_freeze_awarded_streak = IntegerField(default=0)  # streak count when last freeze was awarded
    last_freeze_used_day = CharField(default="")           # ISO date "YYYY-MM-DD" of last consumed freeze

    class Meta:
        table_name = "userstat"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `SessionResult.xp = total * 15` (placeholder) | Per-card `compute_xp_for_review(tier, rating, streak)` | Phase 3 | Rewrites the property; existing test `assert s.xp == 30` must be updated |
| `compute_streak()` — freeze-unaware | `compute_streak_with_freeze()` — reads UserStat | Phase 3 | All callers of `compute_streak()` must switch to new function |
| `build_queue()` — tier-unaware | `build_queue(unlocked_tiers=...)` — filters locked tiers | Phase 3 | Backward compatible: default None = serve all tiers (for `--topic` sessions) |
| `_show_dashboard()` — static placeholder | Live streak + level + due count | Phase 3 | Updates cli.py `_show_dashboard()` |
| `stats()` command — stub | Full Rich Panel with all GAME-05 data | Phase 3 | Replaces stub in cli.py |

**Deprecated/outdated:**
- `xp = self.total * 15` property in `SessionResult` — replaced with per-card accumulation
- Existing `test_session_result_accuracy` assertion `assert s.xp == 30` — will need updating once SessionResult.xp formula changes

## Open Questions

1. **Streak UTC vs. local date semantics**
   - What we know: `ReviewHistory.reviewed_at` is naive UTC; `compute_streak()` uses `.date()` on naive UTC.
   - What's unclear: CONTEXT.md says "calendar day (local date)" but the storage convention is UTC.
   - Recommendation: Use UTC-day convention consistently (document it); don't change storage in Phase 3. The user is unlikely to review at times where UTC-day != local-day for a solo tool.

2. **XP total recompute performance**
   - What we know: Total XP = sum over all ReviewHistory rows; daily cap = 25; at 25 cards/day for 365 days = ~9,125 rows maximum in one year.
   - What's unclear: Whether the streak-at-time-of-review matters for historical XP or whether today's streak is applied retroactively.
   - Recommendation: Apply today's streak to all historical rows (motivational tool, not audit trail). 9,125 rows with Python-level iteration is fast enough; no SQL aggregation optimization needed.

3. **Freeze awarded logic: when exactly does the freeze award trigger?**
   - What we know: "Earned every 7 consecutive days" — but at what moment? At the moment the 7th-day review happens? At the start of day 8?
   - What's unclear: The CONTEXT.md says "every 7 consecutive days" without specifying the trigger point.
   - Recommendation: Award the freeze at the end of a session (in `_show_summary`) when streak transitions from 6 to 7, 13 to 14, etc. Check `streak % 7 == 0 and streak > 0` after the session to award.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (configured in pyproject.toml) |
| Config file | pyproject.toml `[tool.pytest.ini_options]` — testpaths=["tests"], addopts="-x -q" |
| Quick run command | `python -m pytest tests/test_gamification.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| GAME-01 | `compute_xp_for_review(tier, rating, streak)` returns correct values for all combinations | unit | `python -m pytest tests/test_gamification.py::test_xp_formula -x` | ❌ Wave 0 |
| GAME-01 | `SessionResult.xp` accumulates per-card XP correctly across a session | unit | `python -m pytest tests/test_gamification.py::test_session_xp_accumulation -x` | ❌ Wave 0 |
| GAME-01 | Streak multiplier caps at +50% at day 35+ | unit | `python -m pytest tests/test_gamification.py::test_streak_multiplier_cap -x` | ❌ Wave 0 |
| GAME-02 | `compute_streak_with_freeze()` returns correct streak for consecutive days | unit | `python -m pytest tests/test_gamification.py::test_streak_consecutive -x` | ❌ Wave 0 |
| GAME-02 | Streak resets to 0 when no review yesterday and no freeze available | unit | `python -m pytest tests/test_gamification.py::test_streak_resets_no_freeze -x` | ❌ Wave 0 |
| GAME-03 | Freeze consumed automatically on missed day; count decrements | unit | `python -m pytest tests/test_gamification.py::test_freeze_consumed -x` | ❌ Wave 0 |
| GAME-03 | Freeze awarded after 7-day streak milestone | unit | `python -m pytest tests/test_gamification.py::test_freeze_awarded -x` | ❌ Wave 0 |
| GAME-04 | `get_level_info(xp)` returns correct level/name for known XP values | unit | `python -m pytest tests/test_gamification.py::test_level_derivation -x` | ❌ Wave 0 |
| GAME-04 | Max level shows "DevOps Architect" and `is_max=True` | unit | `python -m pytest tests/test_gamification.py::test_max_level -x` | ❌ Wave 0 |
| GAME-05 | `hms stats` command renders without error on empty DB | unit | `python -m pytest tests/test_cli.py::test_stats_empty -x` | ❌ Wave 0 |
| GAME-05 | `hms stats` shows streak, level, XP bar in output | unit | `python -m pytest tests/test_cli.py::test_stats_with_data -x` | ❌ Wave 0 |
| ADAPT-01 | Tier shown in question display (already passing from Phase 2) | unit | `python -m pytest tests/test_quiz.py -x -q` | ✅ |
| ADAPT-02 | `is_tier_unlocked('topic', 'L2')` returns False when <80% L1 mastered | unit | `python -m pytest tests/test_gamification.py::test_tier_locked -x` | ❌ Wave 0 |
| ADAPT-02 | `is_tier_unlocked('topic', 'L2')` returns True when ≥80% L1 mastered | unit | `python -m pytest tests/test_gamification.py::test_tier_unlocked -x` | ❌ Wave 0 |
| ADAPT-03 | L3 unlock follows same pattern as L2 with L2 prerequisite | unit | `python -m pytest tests/test_gamification.py::test_l3_unlock -x` | ❌ Wave 0 |
| ADAPT-04 | `build_queue()` excludes locked-tier cards for topics | unit | `python -m pytest tests/test_quiz.py::test_build_queue_respects_unlock -x` | ❌ Wave 0 |
| ADAPT-04 | Unlock notification appears in session summary when tier newly unlocked | unit | `python -m pytest tests/test_quiz.py::test_unlock_notification -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_gamification.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_gamification.py` — covers GAME-01 through GAME-04, ADAPT-02 through ADAPT-04
- [ ] `src/hms/gamification.py` — new module (stub or first wave)
- [ ] `UserStat` table registration in `ensure_initialized()` — `db.create_tables([Card, ReviewHistory, UserStat], safe=True)`
- [ ] Update `conftest.py` to include `UserStat` in `db.create_tables()` call

## Sources

### Primary (HIGH confidence)
- Direct code reading: `src/hms/models.py`, `src/hms/quiz.py`, `src/hms/cli.py`, `src/hms/scheduler.py`, `src/hms/config.py`, `src/hms/init.py` — full implementation read
- `tests/conftest.py`, `tests/test_quiz.py` — test infrastructure patterns confirmed
- `.planning/phases/03-gamification-adaptive-difficulty/03-CONTEXT.md` — all locked decisions read verbatim
- `.planning/REQUIREMENTS.md` — all GAME-01→GAME-05, ADAPT-01→ADAPT-04 requirements read

### Secondary (MEDIUM confidence)
- Rich documentation (from prior context): `Panel`, `Table`, static string output patterns — consistent with existing code usage
- Peewee ORM patterns: `.where()`, `.count()`, `.select()` with compound conditions — consistent with existing code in quiz.py and init.py

### Tertiary (LOW confidence)
- None — all findings derive from direct code reading or locked CONTEXT.md decisions

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries already installed and in use; confirmed by reading source files
- Architecture: HIGH — new module pattern follows established conventions; confirmed by reading existing module structure
- Pitfalls: HIGH for UTC/freeze/xp-accumulation issues (derived from actual code); MEDIUM for mastery edge cases (logic analysis, not tested)
- Test map: HIGH for existing tests; MEDIUM for new test names (Wave 0 creates them)

**Research date:** 2026-03-15
**Valid until:** 2026-06-15 (stable stdlib + mature libraries; no fast-moving dependencies)
