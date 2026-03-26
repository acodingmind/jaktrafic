from __future__ import annotations

from datetime import date

from app.logic.feed_status import evaluate_feed_status
from app.models.entities import FeedStatusState, GtfsFeedWindow


def test_evaluate_feed_status_is_healthy_inside_feed_window() -> None:
    status = evaluate_feed_status(
        feed_window=GtfsFeedWindow(feed_start_date=date(2026, 3, 1), feed_end_date=date(2026, 3, 31)),
        reference_date=date(2026, 3, 26),
        metadata_source="feed_info.txt",
    )

    assert status.state is FeedStatusState.HEALTHY
    assert "covers 2026-03-26" in status.message


def test_evaluate_feed_status_warns_outside_feed_window() -> None:
    status = evaluate_feed_status(
        feed_window=GtfsFeedWindow(feed_start_date=date(2026, 3, 1), feed_end_date=date(2026, 3, 31)),
        reference_date=date(2026, 4, 5),
        metadata_source="service_calendar",
    )

    assert status.state is FeedStatusState.WARNING
    assert "does not cover 2026-04-05" in status.message


def test_evaluate_feed_status_is_best_effort_when_window_is_missing() -> None:
    status = evaluate_feed_status(
        feed_window=GtfsFeedWindow(),
        reference_date=date(2026, 3, 26),
        metadata_source="service_calendar",
    )

    assert status.state is FeedStatusState.HEALTHY
    assert "best-effort" in status.message
