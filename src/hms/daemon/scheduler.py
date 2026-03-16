"""Scheduler logic for the HackMySkills interrupt daemon.

Provides: notify_job() coroutine (APScheduler job), and guard helpers
_is_within_work_hours() and _daily_reviews_today().
"""
from __future__ import annotations

from datetime import datetime, time


def _is_within_work_hours(cfg: dict) -> bool:
    """Return True if the current local time is within the configured work window.

    Reads work_hours_start and work_hours_end from cfg['daemon'] sub-dict.
    Both are ISO time strings in "HH:MM" format.
    """
    daemon_cfg = cfg.get("daemon", {})
    now = datetime.now().time()
    start = time.fromisoformat(daemon_cfg.get("work_hours_start", "09:00"))
    end = time.fromisoformat(daemon_cfg.get("work_hours_end", "21:00"))
    return start <= now <= end


def _daily_reviews_today(cfg: dict) -> int:
    """Count ReviewHistory rows reviewed today (midnight UTC onwards).

    Used to enforce the daemon daily_cap from cfg['daemon']['daily_cap'].
    """
    from hms.models import ReviewHistory
    today = datetime.utcnow().date()
    today_start = datetime(today.year, today.month, today.day)
    return (
        ReviewHistory.select()
        .where(ReviewHistory.reviewed_at >= today_start)
        .count()
    )


def notify_job() -> None:
    """APScheduler job: send a desktop notification if guards pass.

    Guards (evaluated in order -- return early if any fails):
      1. Within work hours (work_hours_start <= now <= work_hours_end)
      2. Daily cap not yet reached (today's reviews < daemon.daily_cap)

    If all guards pass: pick the next due card as a preview and send
    the desktop notification via send_notification().
    """
    from hms.config import load_config
    from hms.daemon.notifier import send_notification
    from hms.init import ensure_initialized
    from hms.models import Card

    ensure_initialized()
    cfg = load_config()

    if not _is_within_work_hours(cfg):
        return

    daemon_cfg = cfg.get("daemon", {})
    cap = daemon_cfg.get("daily_cap", 10)
    if _daily_reviews_today(cfg) >= cap:
        return

    # Pick next due card as preview (if any)
    from datetime import timezone
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    next_card = (
        Card.select()
        .where(Card.due.is_null(False) & (Card.due <= now_utc))
        .order_by(Card.due.asc())
        .first()
    )
    preview = next_card.question_id if next_card else "Time for a quick review!"
    send_notification(preview)
