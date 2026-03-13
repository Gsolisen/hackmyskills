"""Tests for Peewee models and review history persistence (FOUND-07)."""
import json


def test_card_fsrs_state_roundtrip(hms_home):
    from fsrs import Card as FsrsCard
    from hms.models import Card as CardModel
    fsrs_card = FsrsCard()
    serialized = fsrs_card.to_json()
    db_card = CardModel.create(
        question_id="roundtrip-001",
        question_type="flashcard",
        topic="test",
        tier="L1",
        tags="",
        version_tag="v1.0",
        last_verified="2026-01-01",
        fsrs_state=serialized,
        due=None,
        stability=0.0,
        difficulty=0.0,
        reps=0,
        lapses=0,
        state="New",
    )
    retrieved = CardModel.get(CardModel.question_id == "roundtrip-001")
    assert retrieved.fsrs_state == serialized


def test_review_history_persisted(hms_home):
    from fsrs import Card as FsrsCard, Rating
    from hms.models import Card as CardModel, ReviewHistory
    from hms.scheduler import review_card
    fsrs_card = FsrsCard()
    updated_card, review_log = review_card(fsrs_card, Rating.Good)
    db_card = CardModel.create(
        question_id="test-001",
        question_type="flashcard",
        topic="test",
        tier="L1",
        tags="",
        version_tag="v1.0",
        last_verified="2026-01-01",
        fsrs_state=updated_card.to_json(),
        due=updated_card.due.replace(tzinfo=None) if updated_card.due else None,
        stability=updated_card.stability or 0.0,
        difficulty=updated_card.difficulty or 0.0,
        reps=0,
        lapses=0,
        state=str(updated_card.state),
    )
    ReviewHistory.create(
        card=db_card,
        rating=review_log.rating,
        reviewed_at=review_log.review_datetime.replace(tzinfo=None),
        review_log_json=review_log.to_json(),
    )
    record = ReviewHistory.get(ReviewHistory.card == db_card)
    assert record.rating == Rating.Good.value
    assert len(record.review_log_json) > 0
    parsed = json.loads(record.review_log_json)
    assert parsed["rating"] == Rating.Good.value
