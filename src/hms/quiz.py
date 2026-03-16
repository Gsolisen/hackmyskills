"""Quiz session engine for HackMySkills.

Provides the shared infrastructure used by all Wave 2 question-type handlers:
SessionResult, build_queue, persist_rating, compute_streak, run_session.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from typing import Optional

import fsrs
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from hms.config import load_config
from hms.db import db
from hms.gamification import (
    award_freeze_if_due,
    compute_streak_with_freeze,
    compute_xp_for_review,
    get_unlocked_tiers_per_topic,
)
from hms.loader import load_all_questions
from hms.models import Card, ReviewHistory, UserStat
from hms.scheduler import review_card

console = Console()


# ---------------------------------------------------------------------------
# SessionResult
# ---------------------------------------------------------------------------

@dataclass
class SessionResult:
    """Accumulates per-session statistics."""

    total: int = 0
    correct: int = 0  # Good(3) or Easy(4)
    topic_stats: dict[str, dict] = field(default_factory=dict)
    ratings: list[int] = field(default_factory=list)         # kept for backward compat
    cards_reviewed: list[tuple] = field(default_factory=list)  # (tier, rating_value)

    def record(self, topic: str, rating_value: int, tier: str = "L1") -> None:
        """Record a single card review with its tier for XP calculation."""
        self.total += 1
        is_correct = rating_value >= 3
        if is_correct:
            self.correct += 1
        self.ratings.append(rating_value)
        self.cards_reviewed.append((tier, rating_value))
        ts = self.topic_stats.setdefault(topic, {"total": 0, "correct": 0})
        ts["total"] += 1
        if is_correct:
            ts["correct"] += 1

    @property
    def accuracy_pct(self) -> int:
        """Percentage of correct answers (Good or Easy), 0 if no answers."""
        return round(100 * self.correct / self.total) if self.total else 0

    @property
    def xp(self) -> int:
        """XP earned this session. Computed from per-card tier+rating+streak formula."""
        if not self.cards_reviewed:
            return 0
        streak, _ = compute_streak_with_freeze()
        return sum(
            compute_xp_for_review(tier, rating_value, streak)
            for tier, rating_value in self.cards_reviewed
        )


# ---------------------------------------------------------------------------
# Queue building
# ---------------------------------------------------------------------------

def build_queue(
    daily_cap: int,
    topic: Optional[str] = None,
    unlocked_tiers: Optional[dict] = None,
) -> list[Card]:
    """Build an ordered review queue capped at daily_cap.

    Due cards appear first (ordered by due date ascending), followed by new
    cards (due IS NULL, ordered by topic then id).  If topic is specified,
    only cards for that topic are included.  If unlocked_tiers is provided,
    only cards whose tier is in the unlocked list for that topic are included.

    Args:
        daily_cap: Maximum number of cards to return.
        topic: Optional topic slug to restrict the queue.
        unlocked_tiers: Optional dict mapping topic -> list of unlocked tier strings.
            When provided, cards for locked tiers are excluded from the queue.

    Returns:
        List of Card ORM objects, len <= daily_cap.  Returns [] if topic has
        no cards (topic existence check is the caller's responsibility).
    """
    from functools import reduce
    import operator

    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

    base_due = Card.select()
    base_new = Card.select()

    if topic is not None:
        base_due = base_due.where(Card.topic == topic)
        base_new = base_new.where(Card.topic == topic)

    if unlocked_tiers is not None:
        conditions = [
            (Card.topic == t) & (Card.tier.in_(tiers))
            for t, tiers in unlocked_tiers.items()
        ]
        if conditions:
            unlock_filter = reduce(operator.or_, conditions)
            base_due = base_due.where(unlock_filter)
            base_new = base_new.where(unlock_filter)

    due_cards = list(
        base_due.where(Card.due.is_null(False) & (Card.due <= now))
        .order_by(Card.due.asc())
    )
    new_cards = list(
        base_new.where(Card.due.is_null(True))
        .order_by(Card.topic.asc(), Card.id.asc())
    )

    queue = due_cards + new_cards
    return queue[:daily_cap]


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def persist_rating(db_card: Card, rating: fsrs.Rating) -> None:
    """Apply an FSRS rating to db_card and save both Card and ReviewHistory.

    Uses db.atomic() to ensure Card update and ReviewHistory creation are
    written together — prevents partial saves on Ctrl-C mid-session.

    Args:
        db_card: The ORM Card object to update.
        rating: One of fsrs.Rating.Again/Hard/Good/Easy.
    """
    fsrs_card = fsrs.Card.from_json(db_card.fsrs_state) if db_card.fsrs_state else fsrs.Card()
    updated_fsrs, review_log = review_card(fsrs_card, rating)

    new_due = updated_fsrs.due.replace(tzinfo=None)  # strip UTC-awareness for SQLite
    rating_value = int(rating)

    with db.atomic():
        db_card.fsrs_state = updated_fsrs.to_json()
        db_card.due = new_due
        db_card.stability = updated_fsrs.stability or 0.0
        db_card.difficulty = updated_fsrs.difficulty or 0.0
        db_card.state = updated_fsrs.state.name
        db_card.reps += 1
        if rating_value == 1:  # Again
            db_card.lapses += 1
        db_card.save()

        ReviewHistory.create(
            card=db_card,
            rating=rating_value,
            reviewed_at=datetime.now(timezone.utc).replace(tzinfo=None),
            review_log_json=review_log.to_json(),
        )


# ---------------------------------------------------------------------------
# Streak computation
# ---------------------------------------------------------------------------

def compute_streak() -> int:
    """Return the number of consecutive days (ending today) with at least one review.

    Walks backwards from today using date arithmetic, stopping at the first
    day with no reviews.
    """
    rows = list(ReviewHistory.select().order_by(ReviewHistory.reviewed_at.desc()))
    review_dates: set[date] = {row.reviewed_at.date() for row in rows}

    streak = 0
    current = date.today()
    while current in review_dates:
        streak += 1
        current -= timedelta(days=1)
    return streak


# ---------------------------------------------------------------------------
# Internal rendering helpers
# ---------------------------------------------------------------------------

def _render_progress(console: Console, card_num: int, total: int) -> None:
    """Clear screen and print a dim progress indicator."""
    console.clear()
    filled = int(40 * card_num / total) if total else 0
    pct = int(100 * card_num / total) if total else 0
    console.print(f"Card {card_num}/{total} {'─' * filled} {pct}%", style="dim")


def _wait_for_key(valid_keys: set[str] | None = None, _readkey=None) -> str:
    """Block until the user presses a key in valid_keys (or any key if None).

    KeyboardInterrupt from Ctrl-C propagates naturally to run_session's
    outer try/except so the session summary is still shown on quit.

    Args:
        valid_keys: If provided, only return when a matching key is pressed.
        _readkey: Injectable readkey function for testing (defaults to readchar.readkey).

    Returns:
        The key that was pressed.
    """
    if _readkey is None:
        import readchar  # lazy import — readchar may not be installed in bare envs
        _readkey = readchar.readkey

    while True:
        key = _readkey()
        if valid_keys is None or key in valid_keys:
            return key


# ---------------------------------------------------------------------------
# Question-type handlers
# ---------------------------------------------------------------------------

def _handle_flashcard(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    """Display a flashcard question, wait for flip keypress, then collect 1-4 rating.

    Args:
        card: The ORM Card object (scheduling state is updated via persist_rating).
        q_data: The question dict from the YAML bank (prompt, answer, topic, etc.).
        session: The current SessionResult accumulator.
        _readkey: Injectable readkey function for tests; defaults to readchar.readkey.
    """
    rating_map = {
        "1": fsrs.Rating.Again,
        "2": fsrs.Rating.Hard,
        "3": fsrs.Rating.Good,
        "4": fsrs.Rating.Easy,
    }

    console.print(f"[dim][{card.topic} · {card.tier}][/dim]")
    console.print(Panel(q_data["front"], border_style="blue", title="[dim]Question[/dim]"))
    console.print("[dim]Press any key to reveal answer...[/dim]")
    _wait_for_key(_readkey=_readkey)  # any keypress flips
    console.print(Panel(q_data["back"], border_style="green", title="[dim]Answer[/dim]"))
    console.print("[dim]Rate your recall:  1=Again  2=Hard  3=Good  4=Easy[/dim]")
    key = _wait_for_key(valid_keys={"1", "2", "3", "4"}, _readkey=_readkey)
    rating = rating_map[key]
    persist_rating(card, rating)
    session.record(card.topic, rating.value, tier=card.tier)


def _handle_command_fill(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    """Display a command-fill prompt, accept typed answer, report correct/incorrect.

    Uses case-insensitive exact match only (no fuzzy matching).

    Args:
        card: The ORM Card object.
        q_data: The question dict from the YAML bank (prompt, command, etc.).
        session: The current SessionResult accumulator.
        _readkey: Unused for command-fill (kept for consistent handler signature).
    """
    console.print(f"[dim][{card.topic} · {card.tier}][/dim]")
    console.print(Panel(q_data["prompt"], border_style="blue", title="[dim]Fill in the command[/dim]"))
    user_answer = input("$ ").strip()
    canonical = q_data["command"].strip()
    correct = user_answer.lower() == canonical.lower()

    if correct:
        console.print("[bold green]\u2713 Correct![/bold green]")
        rating = fsrs.Rating.Good
    else:
        console.print(
            f"[bold red]\u2717 Incorrect.[/bold red]  Correct answer: [cyan]{canonical}[/cyan]"
        )
        rating = fsrs.Rating.Again

    persist_rating(card, rating)
    session.record(card.topic, rating.value, tier=card.tier)


def _handle_scenario(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    """Display a scenario question, accept A/B/C/D keypress, show result and explanation.

    Shows the situation in a blue Panel, lists the four choices, waits for a
    single keypress in {a,b,c,d,A,B,C,D}, immediately renders correct/incorrect
    feedback, shows the explanation panel, waits for any key to continue, then
    persists the FSRS rating and records to the session.

    Args:
        card: ORM Card whose FSRS state will be updated.
        q_data: Question dict with keys: situation, choices, correct, explanation.
        session: Accumulates per-session statistics.
        _readkey: Injectable key-reader for testing (defaults to readchar.readkey).
    """
    rating_map = {
        "1": fsrs.Rating.Again,
        "2": fsrs.Rating.Hard,
        "3": fsrs.Rating.Good,
        "4": fsrs.Rating.Easy,
    }

    console.print(f"[dim][{card.topic} · {card.tier}][/dim]")
    console.print(Panel(q_data["situation"], border_style="blue", title="[dim]Scenario[/dim]"))
    console.print(f"\n[bold]{q_data['question']}[/bold]\n")
    console.print("[dim]Press any key to reveal answer...[/dim]")
    _wait_for_key(_readkey=_readkey)
    console.print(Panel(q_data["answer"], border_style="green", title="[dim]Answer[/dim]"))
    console.print(Panel(q_data["explanation"], border_style="dim", title="[dim]Explanation[/dim]"))
    console.print("[dim]Rate your recall:  1=Again  2=Hard  3=Good  4=Easy[/dim]")
    key = _wait_for_key(valid_keys={"1", "2", "3", "4"}, _readkey=_readkey)
    rating = rating_map[key]
    persist_rating(card, rating)
    session.record(card.topic, rating.value, tier=card.tier)


def _handle_explain_concept(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    """Display an explain-concept question, accept free-text, show model answer, record self-rating.

    Shows the prompt in a blue Panel, accepts free-text via input() (not evaluated —
    pure self-reflection), shows the model answer in a green Panel, waits for a 1-4
    keypress for self-rating (Again/Hard/Good/Easy), then persists FSRS state and
    records to the session.

    Args:
        card: ORM Card whose FSRS state will be updated.
        q_data: Question dict with keys: prompt, model_answer.
        session: Accumulates per-session statistics.
        _readkey: Injectable key-reader for testing (defaults to readchar.readkey).
    """
    console.print(f"[dim][{card.topic} · {card.tier}][/dim]")
    console.print(Panel(q_data["concept"], border_style="blue", title="[dim]Explain[/dim]"))
    input("Your explanation: ")  # not evaluated — shown for self-reflection only
    console.print(Panel(q_data["model_answer"], border_style="green", title="[dim]Model Answer[/dim]"))
    console.print("[dim]How well did you do?  1=Again  2=Hard  3=Good  4=Easy[/dim]")

    key = _wait_for_key(valid_keys={"1", "2", "3", "4"}, _readkey=_readkey)
    rating_map = {
        "1": fsrs.Rating.Again,
        "2": fsrs.Rating.Hard,
        "3": fsrs.Rating.Good,
        "4": fsrs.Rating.Easy,
    }
    rating = rating_map[key]

    persist_rating(card, rating)
    session.record(card.topic, rating.value, tier=card.tier)


# ---------------------------------------------------------------------------
# Session summary
# ---------------------------------------------------------------------------

def _show_summary(
    session: SessionResult,
    is_partial: bool = False,
    new_unlocks: Optional[list] = None,
) -> None:
    """Print a Rich Panel summarising the session.

    Shows cards reviewed, accuracy, XP (bold yellow), streak, and due-tomorrow
    count.  A per-topic breakdown table is appended only when the session
    spanned more than one topic *and* is not partial.  Unlock notifications are
    shown after the main panel when new_unlocks is non-empty.

    Args:
        session: Accumulated session statistics.
        is_partial: True when the session was interrupted (Ctrl-C); shows a
            condensed mini-summary without the due-tomorrow count or per-topic
            table.
        new_unlocks: Optional list of (topic, tier) tuples for tiers that
            newly unlocked during this session.
    """
    if session.total == 0:
        return  # no summary for zero-card sessions

    streak, freeze_count = compute_streak_with_freeze()

    # Due-tomorrow count
    tomorrow = date.today() + timedelta(days=1)
    tom_start = datetime(tomorrow.year, tomorrow.month, tomorrow.day)
    tom_end = datetime(tomorrow.year, tomorrow.month, tomorrow.day, 23, 59, 59)
    due_tomorrow = Card.select().where(Card.due.between(tom_start, tom_end)).count()

    title = "Session Paused" if is_partial else "Session Complete"
    xp_display = f"[bold yellow]+{session.xp} XP[/bold yellow]"
    streak_display = f"\U0001f525 {streak} day streak" if streak > 0 else "Start a streak today!"
    if freeze_count > 0:
        streak_display += f"  (Freezes: {freeze_count})"

    lines = [
        f"[bold]{session.total}[/bold] cards reviewed",
        f"Accuracy: [bold]{session.accuracy_pct}%[/bold]",
        f"XP earned: {xp_display}",
        f"Streak: {streak_display}",
    ]
    if not is_partial:
        lines.append(f"Next session: [dim]{due_tomorrow} cards due tomorrow[/dim]")

    content = "\n".join(lines)
    console.print(Panel(content, title=f"[bold]{title}[/bold]", border_style="cyan"))

    # Unlock notifications
    if new_unlocks:
        for t, tier in new_unlocks:
            console.print(
                f"[bold green]\U0001f513 {tier} {t} unlocked! Harder cards are now available.[/bold green]"
            )

    # Per-topic breakdown — only for multi-topic full sessions
    if not is_partial and len(session.topic_stats) > 1:
        table = Table(title="By Topic", show_header=True, header_style="bold")
        table.add_column("Topic")
        table.add_column("Cards", justify="right")
        table.add_column("Accuracy", justify="right")
        for topic_name, stats in session.topic_stats.items():
            acc = round(100 * stats["correct"] / stats["total"]) if stats["total"] else 0
            table.add_row(topic_name, str(stats["total"]), f"{acc}%")
        console.print(table)


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

_HANDLER_DISPATCH = {
    "flashcard": _handle_flashcard,
    "command-fill": _handle_command_fill,
    "scenario": _handle_scenario,
    "explain-concept": _handle_explain_concept,
}


def run_session(topic: Optional[str] = None, _readkey=None, max_cards: Optional[int] = None) -> None:
    """Run a full (or partial) quiz session.

    Loads config for daily_cap, builds the queue, then iterates cards
    dispatching to the appropriate handler by question_type.  Ctrl-C exits
    cleanly and still shows the summary for any already-reviewed cards.

    All question dicts are loaded once at session start and stored in a lookup
    dict keyed by question_id to avoid per-card YAML re-reads.  Cards whose
    question_id is not present in the loader output are skipped with a dim
    warning.

    Args:
        topic: Optional topic slug to restrict the session queue.
        _readkey: Injectable readkey function forwarded to handlers (for tests).
    """
    config = load_config()
    daily_cap: int = config["daily_cap"]
    if max_cards is not None:
        daily_cap = min(daily_cap, max_cards)

    # Topic existence check — display a friendly error panel instead of raising
    if topic is not None:
        topic_count = Card.select().where(Card.topic == topic).count()
        if topic_count == 0:
            console.print(Panel(
                f"No cards found for topic '[bold]{topic}[/bold]'.\n"
                "Run [bold]hms topics[/bold] to see available topics.",
                border_style="red",
            ))
            return

    # Snapshot unlock status before session for post-session diff
    unlocks_before = get_unlocked_tiers_per_topic() if topic is None else {}

    # For no-topic sessions: pass unlock status to queue builder
    unlocked_tiers = unlocks_before if topic is None else None
    queue = build_queue(daily_cap, topic, unlocked_tiers=unlocked_tiers)
    if not queue:
        console.print("Nothing to review right now — come back tomorrow!")
        return

    all_questions = load_all_questions()
    questions_by_id = {q["id"]: q for q in all_questions}

    session = SessionResult()
    total = len(queue)

    try:
        for idx, card in enumerate(queue, start=1):
            _render_progress(console, idx, total)
            q_data = questions_by_id.get(card.question_id)
            if q_data is None:
                console.print(
                    f"[dim]Skipping {card.question_id} — question data not found in loader.[/dim]"
                )
                continue
            handler = _HANDLER_DISPATCH.get(card.question_type)
            if handler is None:
                console.print(f"[dim]Unknown question type: {card.question_type} — skipping.[/dim]")
                continue
            handler(card, q_data, session, _readkey)
    except KeyboardInterrupt:
        console.print()  # newline after ^C
        _show_summary(session, is_partial=True, new_unlocks=[])
        return

    # Award freeze if streak milestone reached
    streak, _ = compute_streak_with_freeze()
    stat, _ = UserStat.get_or_create(id=1)
    award_freeze_if_due(streak, stat)

    # Compute newly unlocked tiers
    unlocks_after = get_unlocked_tiers_per_topic() if topic is None else {}
    new_unlocks: list = []  # [(topic, tier), ...]
    for t, tiers in unlocks_after.items():
        before_tiers = unlocks_before.get(t, [])
        for tier in tiers:
            if tier not in before_tiers:
                new_unlocks.append((t, tier))

    _show_summary(session, is_partial=False, new_unlocks=new_unlocks)
