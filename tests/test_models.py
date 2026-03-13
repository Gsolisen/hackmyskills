"""Tests for Peewee models and review history persistence (FOUND-07). Stubs for Plan 01-02."""
import pytest


@pytest.mark.xfail(reason="hms.models not yet created — will be implemented in Plan 01-02")
def test_review_history_persisted(hms_home):
    from hms.db import db
    from hms.models import Card as CardModel, ReviewHistory
    from hms.init import ensure_initialized
    ensure_initialized()
    # Real assertions will be added in Plan 01-02
    pass


@pytest.mark.xfail(reason="hms.models not yet created — will be implemented in Plan 01-02")
def test_card_fsrs_state_roundtrip(hms_home):
    pass
