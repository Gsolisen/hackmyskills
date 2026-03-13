"""Tests for the FSRS scheduling wrapper (FOUND-06)."""
from fsrs import Card, Rating
from hms.scheduler import review_card


def test_review_updates_due():
    card = Card()
    updated, log = review_card(card, Rating.Good)
    assert updated.due is not None
    assert updated.due.tzinfo is not None  # must be UTC-aware


def test_all_ratings_accepted():
    for rating in [Rating.Again, Rating.Hard, Rating.Good, Rating.Easy]:
        card = Card()
        updated, _ = review_card(card, rating)
        assert updated.due is not None
        assert updated.due.tzinfo is not None


def test_review_log_has_rating():
    card = Card()
    _, log = review_card(card, Rating.Easy)
    assert log.rating == Rating.Easy.value
    assert len(log.to_json()) > 0
