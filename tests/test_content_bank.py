"""Tests for content bank completeness (CONT-01 through CONT-04, EXT-01)."""
from __future__ import annotations
from pathlib import Path

from hms.loader import load_questions, load_all_questions, REQUIRED_BASE_FIELDS

CONTENT_DIR = Path(__file__).resolve().parent.parent / "src" / "hms" / "content"
TOPICS = ["kubernetes", "terraform", "cicd", "bash", "aws"]


def _load_topic(topic: str) -> list[dict]:
    return load_questions(CONTENT_DIR / f"{topic}.yaml")


def test_l1_count_per_topic():
    """CONT-01: Each topic has >= 30 L1 cards."""
    for topic in TOPICS:
        qs = _load_topic(topic)
        l1 = sum(1 for q in qs if q["tier"] == "L1")
        assert l1 >= 30, f"{topic} has {l1} L1 cards, need >= 30"


def test_l2_count_per_topic():
    """CONT-02: Each topic has >= 10 L2 cards."""
    for topic in TOPICS:
        qs = _load_topic(topic)
        l2 = sum(1 for q in qs if q["tier"] == "L2")
        assert l2 >= 10, f"{topic} has {l2} L2 cards, need >= 10"


def test_l3_count_per_topic():
    """CONT-03: Each topic has >= 5 L3 cards."""
    for topic in TOPICS:
        qs = _load_topic(topic)
        l3 = sum(1 for q in qs if q["tier"] == "L3")
        assert l3 >= 5, f"{topic} has {l3} L3 cards, need >= 5"


def test_metadata_fields():
    """CONT-04: All questions have version_tag and last_verified."""
    for topic in TOPICS:
        qs = _load_topic(topic)
        for q in qs:
            assert "version_tag" in q and q["version_tag"], f"{q['id']} missing version_tag"
            assert "last_verified" in q and q["last_verified"], f"{q['id']} missing last_verified"


def test_all_required_base_fields():
    """All questions have all REQUIRED_BASE_FIELDS."""
    for topic in TOPICS:
        qs = _load_topic(topic)
        for q in qs:
            missing = REQUIRED_BASE_FIELDS - q.keys()
            assert not missing, f"{q.get('id', '?')} missing: {missing}"


def test_unique_ids_across_all_files():
    """No duplicate IDs across all content files."""
    all_ids: list[str] = []
    for topic in TOPICS:
        qs = _load_topic(topic)
        all_ids.extend(q["id"] for q in qs)
    assert len(all_ids) == len(set(all_ids)), f"Duplicate IDs found: {len(all_ids)} total, {len(set(all_ids))} unique"


def test_drop_in_yaml_discovery(hms_home):
    """EXT-01: Dropping a YAML file into content dir makes questions available."""
    from hms.init import ensure_initialized
    ensure_initialized()

    # Write a minimal valid YAML file
    custom_yaml = hms_home / "content" / "custom_topic.yaml"
    custom_yaml.write_text(
        'questions:\n'
        '  - id: custom-test-001\n'
        '    type: flashcard\n'
        '    topic: custom_topic\n'
        '    tier: L1\n'
        '    tags: [test]\n'
        '    version_tag: v1\n'
        '    last_verified: "2026-01-01"\n'
        '    front: "Test question"\n'
        '    back: "Test answer"\n'
    )

    qs = load_all_questions(hms_home / "content")
    custom_qs = [q for q in qs if q["topic"] == "custom_topic"]
    assert len(custom_qs) == 1, f"Expected 1 custom question, got {len(custom_qs)}"
    assert custom_qs[0]["id"] == "custom-test-001"
