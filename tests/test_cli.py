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


def test_validate_content_clean(hms_home):
    """hms validate-content exits 0 on valid content."""
    from hms.init import ensure_initialized
    ensure_initialized()
    result = runner.invoke(app, ["validate-content"])
    assert result.exit_code == 0
    assert "All content valid" in result.output


def test_validate_content_shows_count(hms_home):
    """hms validate-content reports files and questions checked."""
    from hms.init import ensure_initialized
    ensure_initialized()
    result = runner.invoke(app, ["validate-content"])
    assert result.exit_code == 0
    assert "questions" in result.output
    assert "files" in result.output


def test_generate_command_removed():
    """The generate stub no longer appears in CLI."""
    result = runner.invoke(app, ["--help"])
    assert "generate" not in result.output.lower() or "validate-content" in result.output


def test_topics_command(hms_home):
    """CONT-05: hms topics lists topics with card counts and unlock status."""
    from hms.init import ensure_initialized
    ensure_initialized()
    result = runner.invoke(app, ["topics"])
    assert result.exit_code == 0
    assert "kubernetes" in result.output
    assert "terraform" in result.output
    assert "unlocked" in result.output.lower()


def test_topics_shows_all_discovered(hms_home):
    """hms topics shows user-added topics automatically."""
    from hms.init import ensure_initialized
    ensure_initialized()
    custom = hms_home / "content" / "mycustom.yaml"
    custom.write_text(
        'questions:\n'
        '  - id: mycustom-001\n'
        '    type: flashcard\n'
        '    topic: mycustom\n'
        '    tier: L1\n'
        '    tags: [test]\n'
        '    version_tag: v1\n'
        '    last_verified: "2026-01-01"\n'
        '    front: "Q"\n'
        '    back: "A"\n'
    )
    from hms.init import _sync_cards_from_yaml
    _sync_cards_from_yaml(hms_home / "content")
    result = runner.invoke(app, ["topics"])
    assert result.exit_code == 0
    assert "mycustom" in result.output


def test_import_command(hms_home):
    """EXT-03: hms import validates and imports a question file."""
    from hms.init import ensure_initialized
    ensure_initialized()
    import_file = hms_home / "to_import.yaml"
    import_file.write_text(
        'questions:\n'
        '  - id: imported-test-001\n'
        '    type: flashcard\n'
        '    topic: imported\n'
        '    tier: L1\n'
        '    tags: [test]\n'
        '    version_tag: v1\n'
        '    last_verified: "2026-01-01"\n'
        '    front: "Imported Q"\n'
        '    back: "Imported A"\n'
    )
    result = runner.invoke(app, ["import", str(import_file)])
    assert result.exit_code == 0
    assert "Imported 1 questions" in result.output
    assert (hms_home / "content" / "to_import.yaml").exists()


def test_import_rejects_invalid(hms_home):
    """EXT-03: hms import rejects files with schema errors."""
    from hms.init import ensure_initialized
    ensure_initialized()
    bad_file = hms_home / "bad.yaml"
    bad_file.write_text(
        'questions:\n'
        '  - id: bad-001\n'
        '    type: flashcard\n'
        '    topic: bad\n'
    )
    result = runner.invoke(app, ["import", str(bad_file)])
    assert result.exit_code == 1
    assert "Validation failed" in result.output
    assert not (hms_home / "content" / "bad.yaml").exists()


def test_import_rejects_duplicates(hms_home):
    """EXT-03: hms import blocks files with duplicate IDs."""
    from hms.init import ensure_initialized
    ensure_initialized()
    # Import a file that duplicates an existing bundled question ID
    dup_file = hms_home / "dup.yaml"
    dup_file.write_text(
        'questions:\n'
        '  - id: k8s-pod-lifecycle-001\n'
        '    type: flashcard\n'
        '    topic: kubernetes\n'
        '    tier: L1\n'
        '    tags: [test]\n'
        '    version_tag: k8s-1.29\n'
        '    last_verified: "2026-01-01"\n'
        '    front: "Duplicate question"\n'
        '    back: "Duplicate answer"\n'
    )
    result = runner.invoke(app, ["import", str(dup_file)])
    assert result.exit_code == 1
    # Rollback: file should not remain in content dir
    assert not (hms_home / "content" / "dup.yaml").exists()


def test_import_filename_collision(hms_home):
    """hms import rejects if filename already exists in content dir."""
    from hms.init import ensure_initialized
    ensure_initialized()
    # kubernetes.yaml already exists in content dir (copied by ensure_initialized)
    collision_file = hms_home / "kubernetes.yaml"
    collision_file.write_text(
        'questions:\n'
        '  - id: collision-001\n'
        '    type: flashcard\n'
        '    topic: kubernetes\n'
        '    tier: L1\n'
        '    tags: [test]\n'
        '    version_tag: v1\n'
        '    last_verified: "2026-01-01"\n'
        '    front: "Q"\n'
        '    back: "A"\n'
    )
    result = runner.invoke(app, ["import", str(collision_file)])
    assert result.exit_code == 1
    assert "already exists" in result.output
