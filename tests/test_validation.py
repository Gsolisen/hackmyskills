"""Tests for content validation module (AI-01 through AI-05)."""
from __future__ import annotations

import pytest
import yaml
from pathlib import Path

from hms.validation import (
    ContentError,
    DuplicatePair,
    ValidationResult,
    find_duplicates,
    validate_content_dir,
)
from hms.loader import validate_question


# --- Helper ---


def _write_yaml(content_dir: Path, filename: str, questions: list[dict]) -> Path:
    """Write a questions YAML file into the given content directory."""
    p = content_dir / filename
    p.write_text(yaml.dump({"questions": questions}, default_flow_style=False))
    return p


def _valid_flashcard(id_: str, front: str = "What is X?", back: str = "X is Y.", **kw):
    """Minimal valid flashcard dict."""
    base = {
        "id": id_,
        "type": "flashcard",
        "topic": "test",
        "tier": "L1",
        "tags": ["test"],
        "version_tag": "v1.0",
        "last_verified": "2026-01-01",
        "front": front,
        "back": back,
    }
    base.update(kw)
    return base


# --- Source field in validate_question ---


def test_source_field_optional():
    """validate_question() passes when source field is missing."""
    q = _valid_flashcard("src-opt-001")
    assert "source" not in q
    validate_question(q)


def test_source_field_curated():
    """validate_question() passes with source='curated'."""
    q = _valid_flashcard("src-cur-001", source="curated")
    validate_question(q)


def test_source_field_ai():
    """validate_question() passes with source='ai'."""
    q = _valid_flashcard("src-ai-001", source="ai")
    validate_question(q)


def test_source_field_invalid():
    """validate_question() raises ValueError for source='unknown'."""
    q = _valid_flashcard("src-bad-001", source="unknown")
    with pytest.raises(ValueError, match="invalid source"):
        validate_question(q)


# --- validate_content_dir ---


def test_validate_content_dir_clean(hms_home):
    """validate_content_dir() returns no errors for valid content dir."""
    content_dir = hms_home / "content"
    _write_yaml(content_dir, "good.yaml", [
        _valid_flashcard("clean-001"),
        _valid_flashcard("clean-002", front="Different Q", back="Different A"),
    ])
    result = validate_content_dir(content_dir)
    assert result.ok
    assert result.files_checked == 1
    assert result.questions_checked == 2
    assert result.errors == []
    assert result.duplicates == []


def test_validate_content_dir_bad_question(hms_home):
    """validate_content_dir() returns ContentError for invalid question."""
    content_dir = hms_home / "content"
    bad_q = {"id": "bad-001", "type": "flashcard", "topic": "test"}
    _write_yaml(content_dir, "bad.yaml", [bad_q])
    result = validate_content_dir(content_dir)
    assert not result.ok
    assert len(result.errors) >= 1
    assert isinstance(result.errors[0], ContentError)
    assert result.errors[0].question_id == "bad-001"


# --- find_duplicates ---


def test_find_duplicates_exact_id():
    """find_duplicates() catches two questions with same ID."""
    q1 = _valid_flashcard("dup-001")
    q2 = _valid_flashcard("dup-001", front="Totally different", back="Also different")
    dupes = find_duplicates([("a.yaml", q1), ("b.yaml", q2)])
    assert len(dupes) >= 1
    assert any(d.reason == "exact_id" for d in dupes)


def test_find_duplicates_token_overlap():
    """find_duplicates() catches two questions with >70% word overlap in text fields."""
    q1 = _valid_flashcard(
        "overlap-001",
        front="What is a Kubernetes pod and how does it work?",
        back="A pod is the smallest deployable unit in Kubernetes",
    )
    q2 = _valid_flashcard(
        "overlap-002",
        front="What is a Kubernetes pod and how does it function?",
        back="A pod is the smallest deployable unit in Kubernetes",
    )
    dupes = find_duplicates([("a.yaml", q1), ("a.yaml", q2)])
    assert len(dupes) >= 1
    assert any(d.reason == "token_overlap" for d in dupes)
    assert any(d.similarity > 0.70 for d in dupes)


def test_find_duplicates_no_false_positive():
    """find_duplicates() does NOT flag questions with <70% word overlap."""
    q1 = _valid_flashcard(
        "nodup-001",
        front="What is a Kubernetes pod?",
        back="A pod is the smallest deployable unit",
    )
    q2 = _valid_flashcard(
        "nodup-002",
        front="How do you configure a Terraform provider?",
        back="Use the provider block in your main.tf file",
    )
    dupes = find_duplicates([("a.yaml", q1), ("b.yaml", q2)])
    assert len(dupes) == 0


def test_validate_content_dir_with_duplicates(hms_home):
    """validate_content_dir() returns DuplicatePair entries for duplicate questions."""
    content_dir = hms_home / "content"
    q1 = _valid_flashcard("valdup-001")
    q2 = _valid_flashcard("valdup-001", front="Something else", back="Something else")
    _write_yaml(content_dir, "dup_test.yaml", [q1, q2])
    result = validate_content_dir(content_dir)
    assert not result.ok
    assert len(result.duplicates) >= 1
    assert isinstance(result.duplicates[0], DuplicatePair)
