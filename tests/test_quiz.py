"""Tests for the quiz session engine (hms.quiz).

Non-xfail tests cover SessionResult, build_queue, and basic run_session behavior.
Handler tests cover flashcard and command-fill flows with mock input injection.
Summary tests cover _show_summary for single-topic, multi-topic, and empty sessions.
"""
from __future__ import annotations

import io
from datetime import datetime, timedelta, timezone
from unittest.mock import patch

import pytest
from rich.console import Console

from hms.quiz import (
    SessionResult,
    _handle_command_fill,
    _handle_explain_concept,
    _handle_flashcard,
    _handle_scenario,
    _show_summary,
    build_queue,
    run_session,
)


# ---------------------------------------------------------------------------
# SessionResult unit tests
# ---------------------------------------------------------------------------

def test_session_result_accuracy(hms_home):
    """accuracy_pct rounds; xp uses per-card formula (L1 Good=5, L1 Again=0)."""
    s = SessionResult()
    s.record("k8s", 3, tier="L1")   # Good — correct; XP = 5
    s.record("k8s", 1, tier="L1")   # Again — incorrect; XP = 0
    assert s.accuracy_pct == 50
    assert s.xp == 5   # 5 + 0 = 5 (no streak yet, streak=0)
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
    """build_queue returns [] for an unknown topic (no ValueError raised).

    Topic existence check moved to run_session() which displays a red Panel.
    """
    result = build_queue(25, topic="missing")
    assert result == []


# ---------------------------------------------------------------------------
# run_session: empty-queue and error-panel paths
# ---------------------------------------------------------------------------

def test_quiz_empty_queue(hms_home):
    """With an empty DB, run_session() returns without raising and prints nothing-to-review."""
    from rich.console import Console
    import hms.quiz as quiz_mod

    captured = io.StringIO()
    test_console = Console(file=captured, highlight=False)

    # Replace the module-level console so run_session uses our StringIO console
    original_console = quiz_mod.console
    quiz_mod.console = test_console
    try:
        run_session()
    finally:
        quiz_mod.console = original_console

    output = captured.getvalue()
    assert "Nothing to review" in output


def test_run_session_unknown_topic(hms_home, monkeypatch):
    """run_session(topic='missing') prints a red Panel and returns without raising."""
    import hms.quiz as quiz_mod

    captured = io.StringIO()
    monkeypatch.setattr("hms.quiz.console", Console(file=captured, highlight=False))
    run_session(topic="missing")  # must not raise
    output = captured.getvalue()
    assert "No cards found" in output


# ---------------------------------------------------------------------------
# _show_summary tests
# ---------------------------------------------------------------------------

def test_show_summary_single_topic(hms_home, monkeypatch):
    """Single-topic session: summary shows cards/XP but NO per-topic table."""
    import hms.quiz as quiz_mod

    captured = io.StringIO()
    monkeypatch.setattr("hms.quiz.console", Console(file=captured, highlight=False))
    session = SessionResult()
    session.record("kubernetes", 3)
    session.record("kubernetes", 4)
    session.record("kubernetes", 1)
    _show_summary(session, is_partial=False)
    output = captured.getvalue()
    assert "3" in output          # cards reviewed count
    assert "XP" in output
    assert "By Topic" not in output  # single topic — no breakdown table


def test_show_summary_multi_topic(hms_home, monkeypatch):
    """Multi-topic session: summary includes per-topic breakdown table."""
    import hms.quiz as quiz_mod

    captured = io.StringIO()
    monkeypatch.setattr("hms.quiz.console", Console(file=captured, highlight=False))
    session = SessionResult()
    session.record("kubernetes", 3)
    session.record("terraform", 1)
    _show_summary(session, is_partial=False)
    output = captured.getvalue()
    assert "By Topic" in output
    assert "kubernetes" in output
    assert "terraform" in output


def test_show_summary_empty(hms_home, monkeypatch):
    """Zero-card session produces no output (early return)."""
    captured = io.StringIO()
    monkeypatch.setattr("hms.quiz.console", Console(file=captured, highlight=False))
    session = SessionResult()  # total = 0
    _show_summary(session)
    output = captured.getvalue()
    assert output.strip() == ""  # nothing printed


# ---------------------------------------------------------------------------
# Handler tests: flashcard flow
# ---------------------------------------------------------------------------

def test_flashcard_flow(hms_home):
    """Full flashcard display and keypress flow.

    Sequence: any key (flip) then '3' (Good). Asserts reps==1, session stats.
    """
    from hms.models import Card
    import hms.quiz as quiz_mod

    # Create a card in the test DB
    card = Card.create(
        question_id="k8s-pod-001",
        question_type="flashcard",
        topic="kubernetes",
        tier="L1",
    )
    q_data = {
        "id": "k8s-pod-001",
        "type": "flashcard",
        "topic": "kubernetes",
        "difficulty_tier": "L1",
        "front": "What is a Pod?",
        "back": "The smallest deployable unit in Kubernetes.",
    }
    session = SessionResult()

    # Build a mock_readkey that yields space (flip), then '3' (Good)
    keys = iter([" ", "3"])

    def mock_readkey():
        return next(keys)

    # Suppress console output
    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        _handle_flashcard(card, q_data, session, _readkey=mock_readkey)
    finally:
        quiz_mod.console = original_console

    # Verify DB state: reps incremented
    card = Card.get_by_id(card.id)
    assert card.reps == 1
    # Verify session: total == 1, correct == 1 (rating 3 = Good >= 3)
    assert session.total == 1
    assert session.correct == 1


# ---------------------------------------------------------------------------
# Handler tests: command-fill flow
# ---------------------------------------------------------------------------

def test_command_fill_correct(hms_home):
    """command-fill: correct answer (exact, case-insensitive) is accepted, rated Good."""
    from hms.models import Card
    import hms.quiz as quiz_mod

    card = Card.create(
        question_id="k8s-cmd-001",
        question_type="command-fill",
        topic="kubernetes",
        tier="L1",
    )
    q_data = {
        "id": "k8s-cmd-001",
        "type": "command-fill",
        "prompt": "List all pods in all namespaces:",
        "command": "kubectl get pods --all-namespaces",
    }
    session = SessionResult()

    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        with patch("builtins.input", return_value="kubectl get pods --all-namespaces"):
            _handle_command_fill(card, q_data, session, _readkey=None)
    finally:
        quiz_mod.console = original_console

    card = Card.get_by_id(card.id)
    assert card.reps == 1
    assert session.correct == 1
    assert session.total == 1


def test_command_fill_incorrect(hms_home):
    """command-fill: wrong answer is rated Again, lapses incremented."""
    from hms.models import Card
    import hms.quiz as quiz_mod

    card = Card.create(
        question_id="k8s-cmd-002",
        question_type="command-fill",
        topic="kubernetes",
        tier="L1",
    )
    q_data = {
        "id": "k8s-cmd-002",
        "type": "command-fill",
        "prompt": "List all pods in all namespaces:",
        "command": "kubectl get pods --all-namespaces",
    }
    session = SessionResult()

    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        with patch("builtins.input", return_value="kubectl pods"):
            _handle_command_fill(card, q_data, session, _readkey=None)
    finally:
        quiz_mod.console = original_console

    card = Card.get_by_id(card.id)
    assert card.lapses == 1
    assert session.correct == 0
    assert session.total == 1


# ---------------------------------------------------------------------------
# Handler tests: scenario flow
# ---------------------------------------------------------------------------

def test_scenario_flow_correct(hms_home):
    """Scenario: correct A/B/C/D keypress is rated Good, reps incremented."""
    from hms.models import Card
    import hms.quiz as quiz_mod

    card = Card.create(
        question_id="tf-scen-001",
        question_type="scenario",
        topic="terraform",
        tier="L2",
    )
    q_data = {
        "id": "tf-scen-001",
        "type": "scenario",
        "topic": "terraform",
        "difficulty_tier": "L2",
        "situation": "Your Terraform apply fails with a state lock error.",
        "question": "What is the correct action to resolve a stuck state lock?",
        "answer": "Run terraform force-unlock",
        "explanation": "terraform force-unlock removes a stuck state lock safely.",
    }
    session = SessionResult()

    # Sequence: 'b' selects correct answer, then any key to continue
    keys = iter([" ", "3"])

    def mock_readkey():
        return next(keys)

    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        _handle_scenario(card, q_data, session, _readkey=mock_readkey)
    finally:
        quiz_mod.console = original_console

    card = Card.get_by_id(card.id)
    assert card.reps == 1
    assert session.total == 1
    assert session.correct == 1  # Good (rating 3) >= 3


def test_scenario_flow_wrong(hms_home):
    """Scenario: wrong keypress is rated Again, lapses incremented."""
    from hms.models import Card
    import hms.quiz as quiz_mod

    card = Card.create(
        question_id="tf-scen-002",
        question_type="scenario",
        topic="terraform",
        tier="L2",
    )
    q_data = {
        "id": "tf-scen-002",
        "type": "scenario",
        "topic": "terraform",
        "difficulty_tier": "L2",
        "situation": "Your Terraform apply fails with a state lock error.",
        "question": "What is the correct action to resolve a stuck state lock?",
        "answer": "Run terraform force-unlock",
        "explanation": "terraform force-unlock removes a stuck state lock safely.",
    }
    session = SessionResult()

    # Sequence: 'a' selects wrong answer, then any key to continue
    keys = iter([" ", "1"])

    def mock_readkey():
        return next(keys)

    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        _handle_scenario(card, q_data, session, _readkey=mock_readkey)
    finally:
        quiz_mod.console = original_console

    card = Card.get_by_id(card.id)
    assert card.lapses == 1
    assert session.total == 1
    assert session.correct == 0  # Again (rating 1) < 3


# Keep the original test name for backward compatibility with plan references
test_scenario_flow = test_scenario_flow_correct


# ---------------------------------------------------------------------------
# Handler tests: explain-concept flow
# ---------------------------------------------------------------------------

def test_explain_concept_flow(hms_home):
    """Explain-concept: free-text accepted, model answer shown, 1-4 rating persists."""
    from hms.models import Card
    import hms.quiz as quiz_mod

    card = Card.create(
        question_id="k8s-exp-001",
        question_type="explain-concept",
        topic="kubernetes",
        tier="L1",
    )
    q_data = {
        "id": "k8s-exp-001",
        "type": "explain-concept",
        "topic": "kubernetes",
        "difficulty_tier": "L1",
        "concept": "Explain what a ConfigMap is and when you'd use it.",
        "model_answer": "A ConfigMap stores non-sensitive configuration data as key-value pairs.",
    }
    session = SessionResult()

    # Mock: '3' = Good rating
    keys = iter([" ", "3"])

    def mock_readkey():
        return next(keys)

    captured = io.StringIO()
    original_console = quiz_mod.console
    quiz_mod.console = Console(file=captured, highlight=False)
    try:
        with patch("builtins.input", return_value="my explanation"):
            _handle_explain_concept(card, q_data, session, _readkey=mock_readkey)
    finally:
        quiz_mod.console = original_console

    card = Card.get_by_id(card.id)
    assert card.reps == 1
    assert session.total == 1
    assert session.correct == 1  # Good (rating 3) >= 3


# ---------------------------------------------------------------------------
# build_queue: unlock-aware tests
# ---------------------------------------------------------------------------

def test_build_queue_respects_unlock(hms_home):
    """build_queue with unlocked_tiers excludes locked-tier cards."""
    from hms.models import Card
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    Card.create(question_id="k-l1", question_type="flashcard", topic="kubernetes",
                tier="L1", due=now - timedelta(hours=1))
    Card.create(question_id="k-l2", question_type="flashcard", topic="kubernetes",
                tier="L2", due=now - timedelta(hours=1))
    queue = build_queue(10, unlocked_tiers={"kubernetes": ["L1"]})
    qids = [c.question_id for c in queue]
    assert "k-l1" in qids
    assert "k-l2" not in qids


def test_build_queue_serves_unlocked_tiers(hms_home):
    """build_queue with unlocked L1+L2 serves both tiers."""
    from hms.models import Card
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    Card.create(question_id="k-l1", question_type="flashcard", topic="kubernetes",
                tier="L1", due=now - timedelta(hours=1))
    Card.create(question_id="k-l2", question_type="flashcard", topic="kubernetes",
                tier="L2", due=now - timedelta(hours=1))
    queue = build_queue(10, unlocked_tiers={"kubernetes": ["L1", "L2"]})
    qids = [c.question_id for c in queue]
    assert "k-l1" in qids
    assert "k-l2" in qids


# ---------------------------------------------------------------------------
# _show_summary: unlock notification test
# ---------------------------------------------------------------------------

def test_unlock_notification_shown(hms_home):
    """_show_summary displays unlock notification when new_unlocks is non-empty."""
    import hms.quiz as q_mod

    s = SessionResult()
    s.record("kubernetes", 3, tier="L1")

    # Capture console output
    buf = io.StringIO()
    old_console = q_mod.console
    q_mod.console = Console(file=buf, highlight=False)
    try:
        q_mod._show_summary(s, is_partial=False, new_unlocks=[("kubernetes", "L2")])
    finally:
        q_mod.console = old_console

    output = buf.getvalue()
    assert "L2" in output
    assert "kubernetes" in output
    assert "unlocked" in output
