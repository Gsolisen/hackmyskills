"""Tests for the quiz session engine (hms.quiz).

Non-xfail tests cover SessionResult, build_queue, and basic run_session behavior.
Handler-dependent tests are marked xfail(strict=False) until Wave 2 implements them.
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone

import pytest

from hms.quiz import (
    SessionResult,
    build_queue,
    run_session,
)


# ---------------------------------------------------------------------------
# SessionResult unit tests
# ---------------------------------------------------------------------------

def test_session_result_accuracy():
    """accuracy_pct rounds to nearest integer; xp = total * 15."""
    s = SessionResult()
    s.record("k8s", 3)   # Good — correct
    s.record("k8s", 1)   # Again — incorrect
    assert s.accuracy_pct == 50
    assert s.xp == 30
    assert s.total == 2


# ---------------------------------------------------------------------------
# build_queue tests
# ---------------------------------------------------------------------------

def _make_card(topic: str, due: datetime | None, question_id: str) -> "Card":
    """Helper: insert a Card into the test DB."""
    from hms.models import Card
    return Card.create(
        question_id=question_id,
        question_type="flashcard",
        topic=topic,
        tier="L1",
    ) if due is None else Card.create(
        question_id=question_id,
        question_type="flashcard",
        topic=topic,
        tier="L1",
        due=due,
    )


def test_build_queue_order(hms_home):
    """Due cards (due <= now) appear before new cards (due IS NULL)."""
    past = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(hours=1)
    _make_card("k8s", past, "k8s-due-001")
    _make_card("k8s", None, "k8s-new-001")

    queue = build_queue(25)
    assert len(queue) == 2
    assert queue[0].question_id == "k8s-due-001"
    assert queue[1].question_id == "k8s-new-001"


def test_daily_cap_from_config(hms_home):
    """build_queue respects the daily_cap argument, not a hard-coded value."""
    for i in range(5):
        _make_card("k8s", None, f"k8s-new-{i:03d}")

    queue = build_queue(3)
    assert len(queue) == 3


def test_build_queue_topic_filter(hms_home):
    """With topic='kubernetes', build_queue returns only kubernetes cards."""
    _make_card("kubernetes", None, "k8s-filter-001")
    _make_card("kubernetes", None, "k8s-filter-002")
    _make_card("terraform", None, "tf-filter-001")

    queue = build_queue(25, topic="kubernetes")
    assert len(queue) == 2
    assert all(c.topic == "kubernetes" for c in queue)


def test_no_cards_for_topic(hms_home):
    """build_queue raises ValueError when the requested topic has no cards."""
    with pytest.raises(ValueError, match="missing"):
        build_queue(25, topic="missing")


# ---------------------------------------------------------------------------
# run_session: empty-queue and error-panel paths
# ---------------------------------------------------------------------------

def test_quiz_empty_queue(hms_home):
    """With an empty DB, run_session() returns without raising and prints nothing-to-review."""
    from rich.console import Console
    import hms.quiz as quiz_mod

    captured = io.StringIO()
    test_console = Console(file=captured, highlight=False)
    monkeypatched_console = test_console

    # Replace the module-level console so run_session uses our StringIO console
    original_console = quiz_mod.console
    quiz_mod.console = test_console
    try:
        run_session()
    finally:
        quiz_mod.console = original_console

    output = captured.getvalue()
    assert "Nothing to review" in output


# ---------------------------------------------------------------------------
# Handler-dependent tests (Wave 2 implements these)
# ---------------------------------------------------------------------------

@pytest.mark.xfail(strict=False, reason="Wave 2 implements flashcard handler")
def test_flashcard_flow(hms_home):
    """Full flashcard display and keypress flow."""
    raise NotImplementedError


@pytest.mark.xfail(strict=False, reason="Wave 2 implements command-fill handler")
def test_command_fill_correct(hms_home):
    """command-fill: correct answer accepted, rating recorded."""
    raise NotImplementedError


@pytest.mark.xfail(strict=False, reason="Wave 2 implements command-fill handler")
def test_command_fill_incorrect(hms_home):
    """command-fill: incorrect answer recorded as Again."""
    raise NotImplementedError


@pytest.mark.xfail(strict=False, reason="Wave 2 implements scenario handler")
def test_scenario_flow(hms_home):
    """Scenario question display and keypress flow."""
    raise NotImplementedError


@pytest.mark.xfail(strict=False, reason="Wave 2 implements explain-concept handler")
def test_explain_concept_flow(hms_home):
    """Explain-concept display and keypress flow."""
    raise NotImplementedError
