"""YAML question loader with validation for HackMySkills.

Provides load_questions() and validate_question() used by the quiz engine.
All question types and required fields are validated at load time to prevent
schema drift between the content files and the quiz engine.
"""
from __future__ import annotations

import yaml
from pathlib import Path
from importlib.resources import files

REQUIRED_BASE_FIELDS = {"id", "type", "topic", "tier", "tags", "version_tag", "last_verified"}
VALID_TYPES = {"flashcard", "scenario", "command-fill", "explain-concept"}
VALID_TIERS = {"L1", "L2", "L3"}
VALID_SOURCES = {"curated", "ai"}

TYPE_REQUIRED_FIELDS = {
    "flashcard": {"front", "back"},
    "command-fill": {"prompt", "command", "accept_partial"},
    "scenario": {"situation", "question", "answer", "explanation"},
    "explain-concept": {"concept", "model_answer"},
}


def validate_question(q: dict) -> None:
    """Validate a single question dict. Raises ValueError on invalid input."""
    missing_base = REQUIRED_BASE_FIELDS - q.keys()
    if missing_base:
        raise ValueError(
            f"Question {q.get('id', '?')} missing required base fields: {sorted(missing_base)}"
        )
    qtype = q["type"]
    if qtype not in VALID_TYPES:
        raise ValueError(
            f"Question {q.get('id', '?')} has unknown type '{qtype}'. "
            f"Valid types: {sorted(VALID_TYPES)}"
        )
    if q["tier"] not in VALID_TIERS:
        raise ValueError(
            f"Question {q.get('id', '?')} has invalid tier '{q['tier']}'. "
            f"Valid tiers: {sorted(VALID_TIERS)}"
        )
    source = q.get("source")
    if source is not None and source not in VALID_SOURCES:
        raise ValueError(
            f"Question {q.get('id', '?')} has invalid source '{source}'. "
            f"Valid sources: {sorted(VALID_SOURCES)}"
        )

    missing_type = TYPE_REQUIRED_FIELDS[qtype] - q.keys()
    if missing_type:
        raise ValueError(
            f"Question {q.get('id', '?')} (type={qtype}) missing fields: {sorted(missing_type)}"
        )


def load_questions(path) -> list[dict]:
    """Load and validate questions from a YAML file path or importlib.resources path."""
    if hasattr(path, "read_bytes"):
        # importlib.resources Traversable
        raw = path.read_bytes()
    else:
        raw = Path(path).read_bytes()
    data = yaml.safe_load(raw)
    questions = data.get("questions", [])
    validated = []
    for q in questions:
        validate_question(q)
        validated.append(q)
    return validated


def load_all_questions(content_dir: "Path | None" = None) -> list[dict]:
    """Load and validate all YAML question files from a directory.

    If content_dir is None, loads from the user's HMS_HOME/content directory.
    Falls back to bundled content if the directory is empty or missing.
    """
    import hms.config as _cfg
    if content_dir is None:
        content_dir = _cfg.HMS_HOME / "content"

    all_questions: list[dict] = []
    yaml_files = sorted(content_dir.glob("*.yaml")) if content_dir.is_dir() else []

    if yaml_files:
        for yaml_path in yaml_files:
            all_questions.extend(load_questions(yaml_path))
    else:
        for resource in get_bundled_content_files():
            all_questions.extend(load_questions(resource))

    return all_questions


def get_bundled_content_files():
    """Yield importlib.resources Traversable objects for bundled YAML files."""
    content_pkg = files("hms.content")
    for resource in content_pkg.iterdir():
        if resource.name.endswith(".yaml"):
            yield resource
