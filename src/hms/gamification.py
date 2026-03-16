"""Gamification logic for HackMySkills.

Owns: XP formula, streak+freeze computation, level derivation,
mastery queries, and tier unlock status. Imported by quiz.py and cli.py.
Never imports from quiz.py (prevents circular imports).
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import Optional

from hms.models import Card, ReviewHistory, UserStat

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

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
MAX_LEVEL = 10
TIER_BASE_XP: dict[str, int] = {"L1": 5, "L2": 10, "L3": 20}
RATING_MULTIPLIER: dict[int, float] = {1: 0.0, 2: 0.5, 3: 1.0, 4: 1.5}
MASTERY_THRESHOLD = 0.80
UNLOCK_PREREQ: dict[str, Optional[str]] = {"L1": None, "L2": "L1", "L3": "L2"}


# ---------------------------------------------------------------------------
# XP formula (GAME-01)
# ---------------------------------------------------------------------------

def compute_xp_for_review(tier: str, rating_value: int, streak: int) -> int:
    """Compute XP earned for a single card review.

    Formula: round(base_tier_xp * rating_multiplier * streak_multiplier)
    Streak multiplier: +10% per 7-day milestone, capped at +50% (5 milestones).
    """
    base = TIER_BASE_XP.get(tier, 5)
    multiplier = RATING_MULTIPLIER.get(rating_value, 0.0)
    milestones = min(streak // 7, 5)
    streak_multiplier = 1.0 + milestones * 0.10
    return round(base * multiplier * streak_multiplier)


def get_total_xp() -> int:
    """Recompute total XP by summing per-review XP across all ReviewHistory rows.

    Applies today's streak multiplier retroactively (motivational tool, not audit trail).
    """
    rows = list(ReviewHistory.select().join(Card))
    if not rows:
        return 0
    streak, _ = compute_streak_with_freeze()
    total = 0
    for row in rows:
        total += compute_xp_for_review(row.card.tier, row.rating, streak)
    return total


# ---------------------------------------------------------------------------
# Level system (GAME-04)
# ---------------------------------------------------------------------------

def get_level_info(total_xp: int) -> dict:
    """Derive level number (1-10), name, and XP progress from total XP.

    Returns dict with keys: level, name, is_max, xp_in_level, xp_to_next, xp_for_level.
    When is_max is True, xp_in_level/xp_to_next/xp_for_level are not present.
    """
    level = min(total_xp // XP_PER_LEVEL + 1, MAX_LEVEL)
    if level >= MAX_LEVEL:
        return {
            "level": MAX_LEVEL,
            "name": LEVEL_NAMES[-1],
            "is_max": True,
            "xp_to_next": 0,
        }
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


# ---------------------------------------------------------------------------
# Streak + freeze (GAME-02, GAME-03)
# ---------------------------------------------------------------------------

def compute_streak_with_freeze() -> tuple[int, int]:
    """Compute current streak, consuming a freeze if yesterday was missed.

    Returns (streak_count, current_freeze_count).

    Algorithm:
    - Walk backwards from today counting consecutive days with >=1 review.
    - If a day is missing:
        * Check if a freeze has already been used on that exact day (last_freeze_used_day).
          If yes: continue the walk (freeze was previously consumed for this gap).
        * If no freeze was used for this day AND freeze count > 0:
          consume the freeze, record last_freeze_used_day, save UserStat, continue the walk.
        * If no freeze available: stop and return current streak count.
    - Only one freeze can bridge one gap at most.
    """
    stat, _ = UserStat.get_or_create(id=1)
    rows = list(ReviewHistory.select().order_by(ReviewHistory.reviewed_at.desc()))
    review_dates: set[date] = {row.reviewed_at.date() for row in rows}

    streak = 0
    freeze_used = False  # track if we've used a freeze during THIS computation call
    current = datetime.utcnow().date()

    while True:
        if current in review_dates:
            streak += 1
            current -= timedelta(days=1)
        else:
            # Missing day
            day_str = current.isoformat()
            if stat.last_freeze_used_day == day_str:
                # Freeze was previously consumed for this exact day — continue walk
                streak += 1
                current -= timedelta(days=1)
            elif not freeze_used and stat.streak_freezes > 0:
                # Consume a freeze for this missed day
                stat.streak_freezes -= 1
                stat.last_freeze_used_day = day_str
                stat.save()
                freeze_used = True
                streak += 1
                current -= timedelta(days=1)
            else:
                break

    return streak, stat.streak_freezes


def award_freeze_if_due(streak: int, stat: UserStat) -> None:
    """Award a freeze if the current streak is at a new 7-day milestone.

    Idempotent: does not award a second freeze for the same milestone.
    Side effect: saves UserStat if a freeze is awarded.

    Args:
        streak: Current streak count.
        stat: UserStat singleton (id=1) — modified in place if award happens.
    """
    if streak > 0 and streak % 7 == 0 and streak > stat.last_freeze_awarded_streak:
        stat.streak_freezes += 1
        stat.last_freeze_awarded_streak = streak
        stat.save()


# ---------------------------------------------------------------------------
# XP bar display helper
# ---------------------------------------------------------------------------

def format_xp_bar(xp_in_level: int, xp_for_level: int, width: int = 10) -> str:
    """Return a static Unicode block character progress bar string.

    Example: format_xp_bar(250, 500) -> "[#####.....] 50%"
    Uses U+2588 (full block) and U+2591 (light shade) for the bar.
    """
    pct = xp_in_level / xp_for_level if xp_for_level else 0
    filled = round(pct * width)
    bar = "\u2588" * filled + "\u2591" * (width - filled)
    pct_int = round(pct * 100)
    return f"[{bar}] {pct_int}%"


# ---------------------------------------------------------------------------
# Mastery + unlock (ADAPT-02, ADAPT-03)
# ---------------------------------------------------------------------------

def mastery_ratio(topic: str, tier: str) -> float:
    """Return fraction of cards in topic+tier that are mastered (state='Review').

    Returns 1.0 if there are no cards in that topic+tier (edge case: treat as mastered).
    """
    total = Card.select().where(Card.topic == topic, Card.tier == tier).count()
    if total == 0:
        return 1.0
    mastered = Card.select().where(
        Card.topic == topic,
        Card.tier == tier,
        Card.state == "Review",
    ).count()
    return mastered / total


def is_tier_unlocked(topic: str, tier: str) -> bool:
    """Return True if the given tier is unlocked for the given topic.

    L1 is always unlocked.
    L2 unlocks when >=80% of L1 cards are mastered.
    L3 unlocks when >=80% of L2 cards are mastered.
    Edge case: if the prerequisite tier has 0 cards, treat as unlocked.
    """
    prereq = UNLOCK_PREREQ.get(tier)
    if prereq is None:
        return True  # L1
    return mastery_ratio(topic, prereq) >= MASTERY_THRESHOLD


def get_unlocked_tiers_per_topic() -> dict[str, list[str]]:
    """Return {topic: [unlocked_tiers]} for all topics with cards in the DB.

    Example: {"kubernetes": ["L1", "L2"], "terraform": ["L1"]}
    """
    topics = [c.topic for c in Card.select(Card.topic).distinct()]
    result: dict[str, list[str]] = {}
    for topic in topics:
        unlocked = []
        for tier in ("L1", "L2", "L3"):
            if is_tier_unlocked(topic, tier):
                unlocked.append(tier)
        result[topic] = unlocked
    return result
