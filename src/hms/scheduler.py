"""Thin FSRS v6 scheduling wrapper for HackMySkills.

Do not hand-roll scheduling logic — the fsrs library implements FSRS-6
with 21 tuned parameters. This module is a minimal pass-through that
keeps the scheduler singleton stable and gives the rest of the codebase
a clean import boundary.
"""
from fsrs import Scheduler, Card, Rating, ReviewLog

scheduler = Scheduler()


def review_card(card: Card, rating: Rating) -> tuple[Card, ReviewLog]:
    """Thin wrapper around fsrs.Scheduler.review_card().

    Returns (updated_card, review_log). The caller is responsible for
    persisting the updated FSRS state and creating a ReviewHistory row.

    Args:
        card: An fsrs.Card object (new or loaded from fsrs_state JSON).
        rating: One of Rating.Again, Rating.Hard, Rating.Good, Rating.Easy.

    Returns:
        A tuple of (updated Card, ReviewLog). updated_card.due is UTC-aware.
    """
    return scheduler.review_card(card, rating)
