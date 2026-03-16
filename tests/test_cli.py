"""Tests for the hms CLI entry point (FOUND-01)."""
from unittest.mock import patch

from typer.testing import CliRunner
from hms.cli import app

runner = CliRunner()


def test_hms_help():
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "HackMySkills" in result.output


def test_hms_version():
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_hms_no_args_shows_dashboard():
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    assert "HackMySkills" in result.output


def test_stats_empty(hms_home):
    """hms stats renders without crash on empty DB."""
    from hms.init import ensure_initialized
    ensure_initialized()
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    assert "Pipeline Rookie" in result.output
    assert "0 cards due today" in result.output


def test_stats_with_data(hms_home):
    """hms stats shows streak, level, XP bar when review data exists."""
    from datetime import datetime
    from hms.init import ensure_initialized
    from hms.models import Card, ReviewHistory
    # Ensure DB is initialized to tmp data.db before inserting test data
    ensure_initialized()
    card = Card.create(
        question_id="test-stats-k-001", question_type="flashcard",
        topic="test_stats_topic", tier="L1", state="Review",
    )
    ReviewHistory.create(
        card=card, rating=3,
        reviewed_at=datetime.utcnow(),
        review_log_json="{}",
    )
    result = runner.invoke(app, ["stats"])
    assert result.exit_code == 0
    # Streak should be 1 (reviewed today)
    assert "1 day" in result.output
    # Level line
    assert "Pipeline Rookie" in result.output
    # XP bar present
    assert "%" in result.output


def test_dashboard_updated(hms_home):
    """hms with no args shows updated dashboard (not static placeholder)."""
    from hms.init import ensure_initialized
    ensure_initialized()
    result = runner.invoke(app, [])
    assert result.exit_code == 0
    # Must not contain the old static Phase 1 placeholder text
    assert "Data home:" not in result.output
    # Must contain the welcome or streak prompt
    assert ("Welcome!" in result.output) or ("Run" in result.output)


def test_interrupt_command(hms_home):
    """hms interrupt invokes run_session with max_cards=1."""
    with patch("hms.quiz.run_session") as mock_run, \
         patch("hms.init.ensure_initialized"):
        result = runner.invoke(app, ["interrupt"])

    assert result.exit_code == 0
    mock_run.assert_called_once_with(max_cards=1)
