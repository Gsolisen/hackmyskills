"""Tests for YAML question loading (FOUND-03, FOUND-04, FOUND-05)."""
import pytest
from pathlib import Path
from importlib.resources import files as resource_files
from hms.loader import load_questions, validate_question, VALID_TYPES, REQUIRED_BASE_FIELDS


def test_load_bundled_kubernetes_questions():
    """FOUND-03: YAML files from bundled content load without error."""
    yaml_path = resource_files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    assert len(questions) > 0


def test_load_bundled_terraform_questions():
    """FOUND-03: terraform.yaml loads without error."""
    yaml_path = resource_files("hms.content").joinpath("terraform.yaml")
    questions = load_questions(yaml_path)
    assert len(questions) > 0


def test_all_question_types_valid():
    """FOUND-04: YAML schema supports all four question types."""
    yaml_path = resource_files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    found_types = {q["type"] for q in questions}
    assert "flashcard" in found_types
    assert "command-fill" in found_types
    assert "scenario" in found_types
    assert "explain-concept" in found_types


def test_missing_base_field_raises():
    """FOUND-05: Question missing required field raises ValueError."""
    bad_question = {
        "id": "bad-001",
        "type": "flashcard",
        "topic": "test",
        # missing: tier, tags, version_tag, last_verified, front, back
    }
    with pytest.raises(ValueError, match="missing required base fields"):
        validate_question(bad_question)


def test_unknown_type_raises():
    """FOUND-04: Unknown question type raises ValueError."""
    bad_question = {
        "id": "bad-type-001",
        "type": "multiple-choice",  # not in VALID_TYPES
        "topic": "test",
        "tier": "L1",
        "tags": [],
        "version_tag": "v1.0",
        "last_verified": "2026-01-01",
    }
    with pytest.raises(ValueError, match="unknown type"):
        validate_question(bad_question)


def test_missing_type_specific_field_raises():
    """FOUND-04: Flashcard without front/back raises ValueError."""
    bad_flashcard = {
        "id": "fc-bad-001",
        "type": "flashcard",
        "topic": "test",
        "tier": "L1",
        "tags": [],
        "version_tag": "v1.0",
        "last_verified": "2026-01-01",
        # missing: front, back
    }
    with pytest.raises(ValueError):
        validate_question(bad_flashcard)


def test_question_ids_are_slug_format():
    """FOUND-05: IDs follow slug format."""
    yaml_path = resource_files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    for q in questions:
        assert "-" in q["id"], f"ID '{q['id']}' is not slug format"
        assert q["id"] == q["id"].lower(), f"ID '{q['id']}' is not lowercase"


def test_all_base_fields_present():
    """FOUND-05: All questions have required base fields."""
    yaml_path = resource_files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    for q in questions:
        for field in REQUIRED_BASE_FIELDS:
            assert field in q, f"Question '{q.get('id')}' missing field '{field}'"


def test_valid_tiers():
    """FOUND-05: All tier values are L1/L2/L3."""
    yaml_path = resource_files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    valid = {"L1", "L2", "L3"}
    for q in questions:
        assert q["tier"] in valid, f"Invalid tier '{q['tier']}' in question '{q['id']}'"
