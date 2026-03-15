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

from hms.config import load_config
from hms.db import db
from hms.loader import load_questions
from hms.models import Card, ReviewHistory
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
    ratings: list[int] = field(default_factory=list)

    def record(self, topic: str, rating_value: int) -> None:
        """Record a single card review."""
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
        """Percentage of correct answers (Good or Easy), 0 if no answers."""
        return round(100 * self.correct / self.total) if self.total else 0

    @property
    def xp(self) -> int:
        """XP earned this session. Phase 3 replaces with tier-weighted formula."""
        return self.total * 15


# ---------------------------------------------------------------------------
# Queue building
# ---------------------------------------------------------------------------

def build_queue(daily_cap: int, topic: Optional[str] = None) -> list[Card]:
    """Build an ordered review queue capped at daily_cap.

    Due cards appear first (ordered by due date ascending), followed by new
    cards (due IS NULL, ordered by topic then id).  If topic is specified,
    only cards for that topic are included; if the topic has zero cards a
    ValueError is raised so the caller can display an error panel.

    Args:
        daily_cap: Maximum number of cards to return.
        topic: Optional topic slug to restrict the queue.

    Returns:
        List of Card ORM objects, len <= daily_cap.

    Raises:
        ValueError: If topic is given but no cards exist for it.
    """
    now = datetime.now(timezone.utc).replace(tzinfo=None)  # naive UTC

    if topic is not None:
        count = Card.select().where(Card.topic == topic).count()
        if count == 0:
            raise ValueError(f"No cards found for topic '{topic}'")

    base_due = Card.select()
    base_new = Card.select()

    if topic is not None:
        base_due = base_due.where(Card.topic == topic)
        base_new = base_new.where(Card.topic == topic)

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
    console.print(Panel(q_data["prompt"], border_style="blue", title="[dim]Question[/dim]"))
    console.print("[dim]Press any key to reveal answer...[/dim]")
    _wait_for_key(_readkey=_readkey)  # any keypress flips
    console.print(Panel(q_data["answer"], border_style="green", title="[dim]Answer[/dim]"))
    console.print("[dim]Rate your recall:  1=Again  2=Hard  3=Good  4=Easy[/dim]")
    key = _wait_for_key(valid_keys={"1", "2", "3", "4"}, _readkey=_readkey)
    rating = rating_map[key]
    persist_rating(card, rating)
    session.record(card.topic, rating.value)


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
    session.record(card.topic, rating.value)


def _handle_scenario(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    raise NotImplementedError("scenario")


def _handle_explain_concept(card: Card, q_data: dict, session: SessionResult, _readkey=None) -> None:
    raise NotImplementedError("explain-concept")


# ---------------------------------------------------------------------------
# Summary stub (Wave 3 implements full summary)
# ---------------------------------------------------------------------------

def _show_summary(session: SessionResult, is_partial: bool = False) -> None:
    raise NotImplementedError("_show_summary")


# ---------------------------------------------------------------------------
# Session runner
# ---------------------------------------------------------------------------

_HANDLER_DISPATCH = {
    "flashcard": _handle_flashcard,
    "command-fill": _handle_command_fill,
    "scenario": _handle_scenario,
    "explain-concept": _handle_explain_concept,
}


def run_session(topic: Optional[str] = None, _readkey=None) -> None:
    """Run a full (or partial) quiz session.

    Loads config for daily_cap, builds the queue, then iterates cards
    dispatching to the appropriate handler by question_type.  Ctrl-C exits
    cleanly and still shows the summary for any already-reviewed cards.

    All question dicts are loaded once at session start and stored in a lookup
    dict keyed by question_id to avoid per-card YAML re-reads.

    Args:
        topic: Optional topic slug to restrict the session queue.
        _readkey: Injectable readkey function forwarded to handlers (for tests).
    """
    config = load_config()
    daily_cap: int = config["daily_cap"]

    try:
        queue = build_queue(daily_cap, topic)
    except ValueError as exc:
        console.print(Panel(str(exc), title="[red]Error[/red]", border_style="red"))
        return

    if not queue:
        console.print("Nothing to review right now — come back tomorrow!")
        return

    all_questions = load_questions()
    questions_by_id = {q["id"]: q for q in all_questions}

    session = SessionResult()
    total = len(queue)
    is_partial = False

    try:
        for idx, card in enumerate(queue, start=1):
            _render_progress(console, idx, total)
            handler = _HANDLER_DISPATCH.get(card.question_type)
            if handler is None:
                raise NotImplementedError(card.question_type)
            q_data = questions_by_id.get(card.question_id, {})
            handler(card, q_data, session, _readkey)
    except KeyboardInterrupt:
        is_partial = True

    if session.total >= 1:
        _show_summary(session, is_partial=is_partial)
