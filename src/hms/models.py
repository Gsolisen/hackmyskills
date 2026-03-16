"""Peewee ORM models for HackMySkills.

Card and ReviewHistory tables. Do NOT call db.create_tables() here —
tables are created after db.init() inside ensure_initialized() in hms.init.
"""
from peewee import (
    CharField,
    DateTimeField,
    FloatField,
    ForeignKeyField,
    IntegerField,
    TextField,
)

from hms.db import BaseModel


class Card(BaseModel):
    """Spaced-repetition card linked to a question in the YAML bank."""

    question_id = CharField(unique=True, index=True)  # e.g. "k8s-pod-lifecycle-001"
    question_type = CharField()                        # flashcard | scenario | command-fill | explain-concept
    topic = CharField(index=True)                      # e.g. "kubernetes"
    tier = CharField()                                 # L1 | L2 | L3
    tags = TextField(default="")                       # comma-separated or JSON array string
    version_tag = CharField(default="")               # e.g. "v1.29"
    last_verified = CharField(default="")             # ISO date string e.g. "2026-01-01"

    # FSRS scheduling state
    fsrs_state = TextField(default="")                # full card.to_json() blob
    due = DateTimeField(null=True, index=True)        # next review datetime (naive UTC for SQLite storage)
    stability = FloatField(default=0.0)               # FSRS stability parameter
    difficulty = FloatField(default=0.0)              # FSRS difficulty parameter
    reps = IntegerField(default=0)                    # total review count (tracked manually)
    lapses = IntegerField(default=0)                  # lapse (Again) count (tracked manually)
    state = CharField(default="New")                  # New | Learning | Review | Relearning

    class Meta:
        table_name = "card"


class ReviewHistory(BaseModel):
    """One row per review event, linked to the reviewed Card."""

    card = ForeignKeyField(Card, backref="reviews")
    rating = IntegerField()        # 1=Again 2=Hard 3=Good 4=Easy
    reviewed_at = DateTimeField()  # naive UTC datetime of the review
    review_log_json = TextField()  # review_log.to_json() full blob

    class Meta:
        table_name = "reviewhistory"


class UserStat(BaseModel):
    """Single-row table for persistent gamification state (id=1 always).

    streak_freezes: count of available streak freezes
    last_freeze_awarded_streak: streak value when the last freeze was awarded
                                (prevents double-awarding at same milestone)
    last_freeze_used_day: ISO date "YYYY-MM-DD" of the last day a freeze was
                          consumed; empty string if never used
    """
    streak_freezes = IntegerField(default=0)
    last_freeze_awarded_streak = IntegerField(default=0)
    last_freeze_used_day = CharField(default="")

    class Meta:
        table_name = "userstat"
