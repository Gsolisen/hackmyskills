"""Tests for the FSRS scheduling wrapper (FOUND-06). Stubs for Plan 01-02."""
import pytest


@pytest.mark.xfail(reason="hms.scheduler not yet created — will be implemented in Plan 01-02")
def test_review_updates_due():
    from hms.scheduler import review_card
    from fsrs import Card, Rating
    card = Card()
    updated_card, log = review_card(card, Rating.Good)
    assert updated_card.due is not None


@pytest.mark.xfail(reason="hms.scheduler not yet created — will be implemented in Plan 01-02")
def test_all_ratings_accepted():
    from hms.scheduler import review_card
    from fsrs import Card, Rating
    for rating in [Rating.Again, Rating.Hard, Rating.Good, Rating.Easy]:
        card = Card()
        updated, _ = review_card(card, rating)
        assert updated.due is not None
