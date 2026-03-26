from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterator

from app.logic.gtfs_loader import GtfsSource, discover_gtfs_source
from app.logic.service_calendar import ServiceCalendarIndex, load_service_calendar
from app.models.entities import FeedStatus, FeedStatusState, GtfsFeedWindow


GTFS_DATE_FORMAT = "%Y%m%d"
FEED_INFO_REQUIRED_COLUMNS = {"feed_publisher_name", "feed_start_date", "feed_end_date"}


class FeedStatusError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class FeedStatusContext:
    feed_window: GtfsFeedWindow
    feed_status: FeedStatus
    metadata_source: str


def load_feed_status(
    source_path: str | None = None,
    archive_path: str | None = None,
    *,
    reference_date: date | None = None,
    source: GtfsSource | None = None,
    calendar_index: ServiceCalendarIndex | None = None,
) -> FeedStatusContext:
    gtfs_source = source or discover_gtfs_source(source_path=source_path, archive_path=archive_path)
    evaluated_date = reference_date or date.today()
    active_calendar_index = calendar_index or load_service_calendar(source=gtfs_source)

    if gtfs_source.has_file("feed_info.txt"):
        feed_window = _load_feed_window_from_feed_info(gtfs_source)
        metadata_source = "feed_info.txt"
    else:
        feed_window = _build_feed_window_from_calendar(active_calendar_index)
        metadata_source = "service_calendar"

    feed_status = evaluate_feed_status(
        feed_window=feed_window,
        reference_date=evaluated_date,
        metadata_source=metadata_source,
    )
    return FeedStatusContext(
        feed_window=feed_window,
        feed_status=feed_status,
        metadata_source=metadata_source,
    )


def evaluate_feed_status(
    *,
    feed_window: GtfsFeedWindow,
    reference_date: date | None = None,
    metadata_source: str = "feed_info.txt",
) -> FeedStatus:
    evaluated_date = reference_date or date.today()
    start_date = feed_window.feed_start_date
    end_date = feed_window.feed_end_date

    if start_date is None or end_date is None:
        message = (
            f"GTFS feed validity window is unavailable from {metadata_source}; "
            "treat results as best-effort until feed metadata is provided."
        )
        return FeedStatus(
            state=FeedStatusState.HEALTHY,
            message=message,
            feed_start_date=start_date,
            feed_end_date=end_date,
        )

    if start_date <= evaluated_date <= end_date:
        message = (
            f"GTFS feed validity window from {metadata_source} covers {evaluated_date.isoformat()} "
            f"({start_date.isoformat()} to {end_date.isoformat()})."
        )
        return FeedStatus(
            state=FeedStatusState.HEALTHY,
            message=message,
            feed_start_date=start_date,
            feed_end_date=end_date,
        )

    message = (
        f"GTFS feed validity window from {metadata_source} does not cover {evaluated_date.isoformat()} "
        f"({start_date.isoformat()} to {end_date.isoformat()})."
    )
    return FeedStatus(
        state=FeedStatusState.WARNING,
        message=message,
        feed_start_date=start_date,
        feed_end_date=end_date,
    )


def _load_feed_window_from_feed_info(source: GtfsSource) -> GtfsFeedWindow:
    rows = list(_read_feed_info_rows(source))
    if not rows:
        raise FeedStatusError("GTFS file 'feed_info.txt' contains no data rows")
    if len(rows) > 1:
        raise FeedStatusError("GTFS file 'feed_info.txt' must contain exactly one data row")

    row_number, row = rows[0]
    return GtfsFeedWindow(
        feed_publisher_name=_optional_text(row.get("feed_publisher_name", "")),
        feed_version=_optional_text(row.get("feed_version", "")),
        feed_start_date=_parse_optional_gtfs_date(row.get("feed_start_date", ""), row_number=row_number, field_name="feed_start_date"),
        feed_end_date=_parse_optional_gtfs_date(row.get("feed_end_date", ""), row_number=row_number, field_name="feed_end_date"),
    )


def _build_feed_window_from_calendar(calendar_index: ServiceCalendarIndex) -> GtfsFeedWindow:
    if calendar_index.available_date_range is None:
        return GtfsFeedWindow()

    start_date, end_date = calendar_index.available_date_range
    return GtfsFeedWindow(
        feed_publisher_name=None,
        feed_version=None,
        feed_start_date=start_date,
        feed_end_date=end_date,
    )


def _read_feed_info_rows(source: GtfsSource) -> Iterator[tuple[int, dict[str, str]]]:
    header = source.read_header("feed_info.txt")
    missing_columns = sorted(FEED_INFO_REQUIRED_COLUMNS.difference(header))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise FeedStatusError(f"GTFS file 'feed_info.txt' is missing required columns: {missing}")

    with source.open_text("feed_info.txt") as handle:
        reader = csv.DictReader(handle)
        for row_number, raw_row in enumerate(reader, start=2):
            if raw_row is None:
                continue
            if None in raw_row:
                raise FeedStatusError(
                    f"GTFS file 'feed_info.txt' has malformed row {row_number}: column count does not match the header"
                )

            normalized_row = {key: (value or "").strip() for key, value in raw_row.items()}
            if not any(normalized_row.values()):
                continue

            yield row_number, normalized_row


def _parse_optional_gtfs_date(value: str, *, row_number: int, field_name: str) -> date | None:
    value = value.strip()
    if value == "":
        return None

    try:
        return datetime.strptime(value, GTFS_DATE_FORMAT).date()
    except ValueError as exc:
        raise FeedStatusError(
            f"GTFS file 'feed_info.txt' has invalid date '{value}' for '{field_name}' on row {row_number}"
        ) from exc


def _optional_text(value: str) -> str | None:
    cleaned = value.strip()
    return cleaned or None