"""Tests for YAML question loading (FOUND-03, FOUND-04, FOUND-05). Stubs for Plan 01-03."""
import pytest


@pytest.mark.xfail(reason="hms.loader not yet created — will be implemented in Plan 01-03")
def test_load_bundled_questions():
    from hms.loader import load_questions
    from importlib.resources import files
    yaml_path = files("hms.content").joinpath("kubernetes.yaml")
    questions = load_questions(yaml_path)
    assert len(questions) > 0


@pytest.mark.xfail(reason="hms.loader not yet created — will be implemented in Plan 01-03")
def test_all_question_types_valid():
    from hms.loader import load_questions, VALID_TYPES
    # Will be filled with real assertions in Plan 01-03
    pass


@pytest.mark.xfail(reason="hms.loader not yet created — will be implemented in Plan 01-03")
def test_missing_base_field_raises():
    from hms.loader import load_questions
    pass
