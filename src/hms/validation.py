"""Content validation library for HackMySkills.

Provides validate_content_dir() and find_duplicates() for checking YAML
content files against the question schema and detecting duplicate questions
by ID or by token overlap (>70% Jaccard similarity).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class ContentError:
    """A schema validation error for a single question."""

    file: str
    question_id: str
    message: str


@dataclass
class DuplicatePair:
    """A pair of questions flagged as duplicates."""

    id_a: str
    id_b: str
    file_a: str
    file_b: str
    similarity: float  # 0.0-1.0
    reason: str  # "exact_id" or "token_overlap"


@dataclass
class ValidationResult:
    """Aggregated result of content validation."""

    errors: list[ContentError] = field(default_factory=list)
    duplicates: list[DuplicatePair] = field(default_factory=list)
    files_checked: int = 0
    questions_checked: int = 0

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0 and len(self.duplicates) == 0


# --- Token similarity helpers ---

DUPLICATE_THRESHOLD = 0.70


def _tokenize(text: str) -> set[str]:
    """Normalize text into a set of lowercase tokens (length >= 2)."""
    tokens = re.split(r"[\s\W]+", text.lower())
    return {t for t in tokens if len(t) >= 2}


def _token_similarity(text_a: str, text_b: str) -> float:
    """Compute Jaccard similarity between two texts' token sets."""
    set_a = _tokenize(text_a)
    set_b = _tokenize(text_b)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


def _get_question_text(q: dict) -> str:
    """Concatenate all text fields for a question based on its type."""
    qtype = q.get("type", "")
    if qtype == "flashcard":
        return q.get("front", "") + " " + q.get("back", "")
    if qtype == "command-fill":
        return q.get("prompt", "") + " " + q.get("command", "")
    if qtype == "scenario":
        return (
            q.get("situation", "")
            + " "
            + q.get("question", "")
            + " "
            + q.get("answer", "")
        )
    if qtype == "explain-concept":
        return q.get("concept", "") + " " + q.get("model_answer", "")
    # Fallback: join all string values
    return " ".join(str(v) for v in q.values() if isinstance(v, str))


def find_duplicates(questions: list[tuple[str, dict]]) -> list[DuplicatePair]:
    """Detect duplicate questions by exact ID or token overlap.

    Args:
        questions: list of (filename, question_dict) tuples.

    Returns:
        List of DuplicatePair entries for all detected duplicates.
    """
    duplicates: list[DuplicatePair] = []

    # First pass: exact ID duplicates
    id_groups: dict[str, list[tuple[str, dict]]] = {}
    for fname, q in questions:
        qid = q.get("id", "?")
        id_groups.setdefault(qid, []).append((fname, q))

    seen_id_pairs: set[tuple[str, str]] = set()
    for qid, entries in id_groups.items():
        if len(entries) > 1:
            for i in range(len(entries)):
                for j in range(i + 1, len(entries)):
                    fname_a, _ = entries[i]
                    fname_b, _ = entries[j]
                    pair_key = (qid, f"{fname_a}:{fname_b}")
                    if pair_key not in seen_id_pairs:
                        seen_id_pairs.add(pair_key)
                        duplicates.append(
                            DuplicatePair(
                                id_a=qid,
                                id_b=qid,
                                file_a=fname_a,
                                file_b=fname_b,
                                similarity=1.0,
                                reason="exact_id",
                            )
                        )

    # Second pass: token overlap among unique-ID pairs
    unique_questions: list[tuple[str, dict]] = []
    seen_ids: set[str] = set()
    for fname, q in questions:
        qid = q.get("id", "?")
        if qid not in seen_ids:
            seen_ids.add(qid)
            unique_questions.append((fname, q))

    for i in range(len(unique_questions)):
        for j in range(i + 1, len(unique_questions)):
            fname_a, qa = unique_questions[i]
            fname_b, qb = unique_questions[j]
            text_a = _get_question_text(qa)
            text_b = _get_question_text(qb)
            sim = _token_similarity(text_a, text_b)
            if sim > DUPLICATE_THRESHOLD:
                duplicates.append(
                    DuplicatePair(
                        id_a=qa.get("id", "?"),
                        id_b=qb.get("id", "?"),
                        file_a=fname_a,
                        file_b=fname_b,
                        similarity=sim,
                        reason="token_overlap",
                    )
                )

    return duplicates


def validate_content_dir(content_dir: "Path | None" = None) -> ValidationResult:
    """Validate all YAML content files in a directory.

    Checks each question against the schema (via loader.validate_question)
    and detects duplicates by ID and token overlap.

    Args:
        content_dir: Path to content directory. Defaults to HMS_HOME/content.

    Returns:
        ValidationResult with errors, duplicates, and counts.
    """
    from hms.loader import validate_question

    if content_dir is None:
        import hms.config as _cfg

        content_dir = _cfg.HMS_HOME / "content"

    result = ValidationResult()
    all_questions: list[tuple[str, dict]] = []

    yaml_files = sorted(content_dir.glob("*.yaml")) if content_dir.is_dir() else []
    result.files_checked = len(yaml_files)

    for yaml_path in yaml_files:
        try:
            data = yaml.safe_load(yaml_path.read_text())
        except Exception as exc:
            result.errors.append(
                ContentError(
                    file=yaml_path.name,
                    question_id="(file-level)",
                    message=f"YAML parse error: {exc}",
                )
            )
            continue

        questions = data.get("questions", []) if data else []
        for q in questions:
            result.questions_checked += 1
            qid = q.get("id", "?")
            try:
                validate_question(q)
            except ValueError as exc:
                result.errors.append(
                    ContentError(
                        file=yaml_path.name,
                        question_id=qid,
                        message=str(exc),
                    )
                )
            all_questions.append((yaml_path.name, q))

    result.duplicates = find_duplicates(all_questions)
    return result
