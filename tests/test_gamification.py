"""Tests for src/hms/gamification.py.

Covers: XP formula (GAME-01), streak+freeze (GAME-02, GAME-03),
level derivation (GAME-04), mastery/unlock logic (ADAPT-02, ADAPT-03).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta

import pytest

from hms.gamification import (
    LEVEL_NAMES,
    XP_PER_LEVEL,
    award_freeze_if_due,
    compute_streak_with_freeze,
    compute_xp_for_review,
    format_xp_bar,
    get_level_info,
    get_total_xp,
    get_unlocked_tiers_per_topic,
    is_tier_unlocked,
)


# ---------------------------------------------------------------------------
# XP formula tests (GAME-01)
# ---------------------------------------------------------------------------

def test_xp_formula_l1_good_no_streak():
    assert compute_xp_for_review("L1", 3, 0) == 5

def test_xp_formula_l2_easy_no_streak():
    assert compute_xp_for_review("L2", 4, 0) == 15

def test_xp_formula_l3_hard_no_streak():
    assert compute_xp_for_review("L3", 2, 0) == 10

def test_xp_formula_again_is_zero():
    assert compute_xp_for_review("L1", 1, 0) == 0
    assert compute_xp_for_review("L2", 1, 0) == 0
    assert compute_xp_for_review("L3", 1, 0) == 0

def test_streak_multiplier_7_days():
    # 5 * 1.0 * 1.10 = 5.5 -> round to 6
    assert compute_xp_for_review("L1", 3, 7) == 6

def test_streak_multiplier_cap():
    # 5 milestones = +50% max; streak=35 and streak=42 both give same result
    xp_35 = compute_xp_for_review("L1", 3, 35)
    xp_42 = compute_xp_for_review("L1", 3, 42)
    assert xp_35 == xp_42
    # 5 * 1.0 * 1.50 = 7.5 -> 8
    assert xp_35 == 8


# ---------------------------------------------------------------------------
# Level derivation tests (GAME-04)
# ---------------------------------------------------------------------------

def test_level_names_count():
    assert len(LEVEL_NAMES) == 10

def test_xp_per_level():
    assert XP_PER_LEVEL == 500

def test_level_derivation_zero_xp():
    info = get_level_info(0)
    assert info["level"] == 1
    assert info["name"] == "Pipeline Rookie"
    assert info["is_max"] is False

def test_level_derivation_boundary():
    assert get_level_info(499)["level"] == 1
    assert get_level_info(500)["level"] == 2
    assert get_level_info(500)["name"] == "Container Cadet"

def test_level_derivation_mid():
    info = get_level_info(750)
    assert info["level"] == 2
    assert info["xp_in_level"] == 250
    assert info["xp_to_next"] == 250

def test_max_level():
    info = get_level_info(4500)
    assert info["level"] == 10
    assert info["name"] == "DevOps Architect"
    assert info["is_max"] is True

def test_max_level_overflow():
    info = get_level_info(99999)
    assert info["is_max"] is True
    assert info["level"] == 10


# ---------------------------------------------------------------------------
# format_xp_bar tests
# ---------------------------------------------------------------------------

def test_format_xp_bar_half():
    bar = format_xp_bar(250, 500)
    assert "[" in bar and "]" in bar
    assert "50%" in bar

def test_format_xp_bar_zero():
    bar = format_xp_bar(0, 500)
    assert "0%" in bar

def test_format_xp_bar_full():
    bar = format_xp_bar(500, 500)
    assert "100%" in bar


# ---------------------------------------------------------------------------
# Streak tests (GAME-02, GAME-03) — require hms_home fixture for DB access
# ---------------------------------------------------------------------------

def _insert_review(hms_home, days_ago: int, rating: int = 3):
    """Helper: insert a ReviewHistory row N days ago."""
    from hms.models import Card, ReviewHistory
    card, _ = Card.get_or_create(
        question_id=f"test-streak-{days_ago}-{rating}",
        defaults={"question_type": "flashcard", "topic": "k8s", "tier": "L1"},
    )
    reviewed_at = datetime.utcnow().replace(hour=12, minute=0, second=0, microsecond=0)
    reviewed_at -= timedelta(days=days_ago)
    ReviewHistory.create(
        card=card,
        rating=rating,
        reviewed_at=reviewed_at,
        review_log_json="{}",
    )


def test_streak_empty_db(hms_home):
    streak, freezes = compute_streak_with_freeze()
    assert streak == 0
    assert freezes == 0


def test_streak_consecutive(hms_home):
    _insert_review(hms_home, days_ago=0)
    _insert_review(hms_home, days_ago=1)
    _insert_review(hms_home, days_ago=2)
    streak, _ = compute_streak_with_freeze()
    assert streak == 3


def test_streak_resets_no_freeze(hms_home):
    # Reviewed today and 2 days ago — yesterday missed, no freeze
    _insert_review(hms_home, days_ago=0)
    _insert_review(hms_home, days_ago=2)
    streak, _ = compute_streak_with_freeze()
    # Only today counts; yesterday gap stops the walk
    assert streak == 1


def test_freeze_consumed_on_missed_day(hms_home):
    from hms.models import UserStat
    # Set up: reviewed today and 2 days ago (yesterday missed); give 1 freeze
    _insert_review(hms_home, days_ago=0)
    _insert_review(hms_home, days_ago=2)
    stat, _ = UserStat.get_or_create(id=1)
    stat.streak_freezes = 1
    stat.save()

    streak, freezes = compute_streak_with_freeze()
    # Freeze should bridge the gap: 0 days ago + freeze-covers-yesterday + 2 days ago = 3?
    # No: streak walk: today=yes, yesterday=no BUT freeze consumed -> continue, 2-days-ago=yes, 3-days-ago=no -> streak=3
    # Wait: let's verify by logic. If we only have reviews on day=0 and day=2, with a freeze:
    # day 0: yes, day 1: no (use freeze), day 2: yes, day 3: no -> streak = 3
    assert streak == 3
    assert freezes == 0  # freeze was consumed


def test_freeze_awarded(hms_home):
    from hms.models import UserStat
    # award_freeze_if_due should increment freezes when streak is a multiple of 7
    stat, _ = UserStat.get_or_create(id=1)
    initial_freezes = stat.streak_freezes
    award_freeze_if_due(7, stat)
    stat_after, _ = UserStat.get_or_create(id=1)
    assert stat_after.streak_freezes == initial_freezes + 1


def test_freeze_not_awarded_twice_same_milestone(hms_home):
    from hms.models import UserStat
    stat, _ = UserStat.get_or_create(id=1)
    stat.last_freeze_awarded_streak = 7
    stat.streak_freezes = 1
    stat.save()
    award_freeze_if_due(7, stat)
    stat_after, _ = UserStat.get_or_create(id=1)
    # Should NOT award again for same milestone (streak=7 already awarded)
    assert stat_after.streak_freezes == 1


# ---------------------------------------------------------------------------
# Mastery / unlock tests (ADAPT-02, ADAPT-03)
# ---------------------------------------------------------------------------

def _make_card(topic: str, tier: str, state: str, qid: str):
    from hms.models import Card
    return Card.create(
        question_id=qid,
        question_type="flashcard",
        topic=topic,
        tier=tier,
        state=state,
    )


def test_l1_always_unlocked(hms_home):
    assert is_tier_unlocked("kubernetes", "L1") is True


def test_tier_locked_below_threshold(hms_home):
    # 3 L1 cards, 2 mastered (66%) — below 80% threshold
    _make_card("kubernetes", "L1", "Review", "k-1")
    _make_card("kubernetes", "L1", "Review", "k-2")
    _make_card("kubernetes", "L1", "Learning", "k-3")
    assert is_tier_unlocked("kubernetes", "L2") is False


def test_tier_unlocked_at_threshold(hms_home):
    # 5 L1 cards, 4 mastered (80%) — exactly at threshold
    _make_card("kubernetes", "L1", "Review", "k-1")
    _make_card("kubernetes", "L1", "Review", "k-2")
    _make_card("kubernetes", "L1", "Review", "k-3")
    _make_card("kubernetes", "L1", "Review", "k-4")
    _make_card("kubernetes", "L1", "Learning", "k-5")
    assert is_tier_unlocked("kubernetes", "L2") is True


def test_l3_unlock_uses_l2_prereq(hms_home):
    # 5 L2 cards, 4 mastered — L3 should unlock
    _make_card("kubernetes", "L2", "Review", "k-1")
    _make_card("kubernetes", "L2", "Review", "k-2")
    _make_card("kubernetes", "L2", "Review", "k-3")
    _make_card("kubernetes", "L2", "Review", "k-4")
    _make_card("kubernetes", "L2", "New", "k-5")
    assert is_tier_unlocked("kubernetes", "L3") is True


def test_tier_unlocked_zero_prereq_cards(hms_home):
    # No L1 cards in DB for topic — treat as unlocked (avoid ZeroDivisionError)
    assert is_tier_unlocked("terraform", "L2") is True


def test_get_unlocked_tiers_returns_dict(hms_home):
    _make_card("kubernetes", "L1", "Review", "k-1")
    result = get_unlocked_tiers_per_topic()
    assert isinstance(result, dict)
    assert "kubernetes" in result
    assert "L1" in result["kubernetes"]


def test_get_total_xp_empty_db(hms_home):
    assert get_total_xp() == 0
