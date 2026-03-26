from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import date, datetime
from typing import Iterable, Iterator

from app.logic.gtfs_loader import GtfsSource, GtfsSourceError, discover_gtfs_source
from app.models.entities import CalendarDateException, CalendarDateExceptionType, ServiceCalendar


GTFS_DATE_FORMAT = "%Y%m%d"
WEEKDAY_FIELD_NAMES = (
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
)
CALENDAR_REQUIRED_COLUMNS = {
    "service_id",
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
    "start_date",
    "end_date",
}
CALENDAR_DATES_REQUIRED_COLUMNS = {"service_id", "date", "exception_type"}


class ServiceCalendarError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class ServiceCalendarIndex:
    source: GtfsSource
    calendars_by_service_id: dict[str, ServiceCalendar]
    added_dates_by_service_id: dict[str, frozenset[date]]
    removed_dates_by_service_id: dict[str, frozenset[date]]
    available_date_range: tuple[date, date] | None

    def service_ids(self) -> tuple[str, ...]:
        service_ids = set(self.calendars_by_service_id)
        service_ids.update(self.added_dates_by_service_id)
        service_ids.update(self.removed_dates_by_service_id)
        return tuple(sorted(service_ids))

    def is_active(self, service_id: str, on_date: date) -> bool:
        removed_dates = self.removed_dates_by_service_id.get(service_id, frozenset())
        if on_date in removed_dates:
            return False

        added_dates = self.added_dates_by_service_id.get(service_id, frozenset())
        if on_date in added_dates:
            return True

        calendar = self.calendars_by_service_id.get(service_id)
        if calendar is None:
            return False

        if on_date < calendar.start_date or on_date > calendar.end_date:
            return False

        weekday_name = WEEKDAY_FIELD_NAMES[on_date.weekday()]
        return bool(getattr(calendar, weekday_name))

    def active_service_ids(
        self,
        on_date: date,
        candidate_service_ids: Iterable[str] | None = None,
    ) -> tuple[str, ...]:
        service_ids = candidate_service_ids if candidate_service_ids is not None else self.service_ids()
        return tuple(sorted(service_id for service_id in service_ids if self.is_active(service_id, on_date)))


def load_service_calendar(
    source_path: str | None = None,
    archive_path: str | None = None,
    *,
    source: GtfsSource | None = None,
) -> ServiceCalendarIndex:
    gtfs_source = source or discover_gtfs_source(source_path=source_path, archive_path=archive_path)
    if not gtfs_source.has_file("calendar.txt") and not gtfs_source.has_file("calendar_dates.txt"):
        raise ServiceCalendarError(
            "GTFS feed must provide at least one of 'calendar.txt' or 'calendar_dates.txt'"
        )

    calendars_by_service_id = _load_calendar_rows(gtfs_source)
    exceptions_by_service_id = _load_calendar_date_exceptions(gtfs_source)

    merged_calendars: dict[str, ServiceCalendar] = {}
    for service_id, calendar in calendars_by_service_id.items():
        merged_calendars[service_id] = calendar.model_copy(
            update={"exceptions": tuple(exceptions_by_service_id.get(service_id, ()))},
        )

    added_dates_by_service_id: dict[str, frozenset[date]] = {}
    removed_dates_by_service_id: dict[str, frozenset[date]] = {}
    for service_id, exceptions in exceptions_by_service_id.items():
        added_dates_by_service_id[service_id] = frozenset(
            exception.date for exception in exceptions if exception.exception_type == CalendarDateExceptionType.ADDED
        )
        removed_dates_by_service_id[service_id] = frozenset(
            exception.date for exception in exceptions if exception.exception_type == CalendarDateExceptionType.REMOVED
        )

    available_date_range = _derive_available_date_range(
        calendars_by_service_id=merged_calendars,
        exceptions_by_service_id=exceptions_by_service_id,
    )

    return ServiceCalendarIndex(
        source=gtfs_source,
        calendars_by_service_id=merged_calendars,
        added_dates_by_service_id=added_dates_by_service_id,
        removed_dates_by_service_id=removed_dates_by_service_id,
        available_date_range=available_date_range,
    )


def _load_calendar_rows(source: GtfsSource) -> dict[str, ServiceCalendar]:
    if not source.has_file("calendar.txt"):
        return {}

    calendars_by_service_id: dict[str, ServiceCalendar] = {}
    for row_number, row in _read_rows(source, "calendar.txt", required_columns=CALENDAR_REQUIRED_COLUMNS):
        service_id = _get_required_text(row, "calendar.txt", row_number, "service_id")
        if service_id in calendars_by_service_id:
            raise ServiceCalendarError(
                f"GTFS file 'calendar.txt' contains duplicate service_id '{service_id}' on row {row_number}"
            )

        calendar = ServiceCalendar(
            service_id=service_id,
            monday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "monday"), "calendar.txt", row_number, "monday"),
            tuesday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "tuesday"), "calendar.txt", row_number, "tuesday"),
            wednesday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "wednesday"), "calendar.txt", row_number, "wednesday"),
            thursday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "thursday"), "calendar.txt", row_number, "thursday"),
            friday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "friday"), "calendar.txt", row_number, "friday"),
            saturday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "saturday"), "calendar.txt", row_number, "saturday"),
            sunday=_parse_gtfs_flag(_get_required_text(row, "calendar.txt", row_number, "sunday"), "calendar.txt", row_number, "sunday"),
            start_date=_parse_gtfs_date(_get_required_text(row, "calendar.txt", row_number, "start_date"), "calendar.txt", row_number, "start_date"),
            end_date=_parse_gtfs_date(_get_required_text(row, "calendar.txt", row_number, "end_date"), "calendar.txt", row_number, "end_date"),
        )
        calendars_by_service_id[service_id] = calendar

    return calendars_by_service_id


def _load_calendar_date_exceptions(
    source: GtfsSource,
) -> dict[str, tuple[CalendarDateException, ...]]:
    if not source.has_file("calendar_dates.txt"):
        return {}

    exceptions: dict[str, list[CalendarDateException]] = {}
    for row_number, row in _read_rows(
        source,
        "calendar_dates.txt",
        required_columns=CALENDAR_DATES_REQUIRED_COLUMNS,
    ):
        service_id = _get_required_text(row, "calendar_dates.txt", row_number, "service_id")
        exception = CalendarDateException(
            service_id=service_id,
            date=_parse_gtfs_date(_get_required_text(row, "calendar_dates.txt", row_number, "date"), "calendar_dates.txt", row_number, "date"),
            exception_type=_parse_exception_type(
                _get_required_text(row, "calendar_dates.txt", row_number, "exception_type"),
                row_number=row_number,
            ),
        )
        exceptions.setdefault(service_id, []).append(exception)

    return {
        service_id: tuple(sorted(items, key=lambda item: (item.date, item.exception_type.value)))
        for service_id, items in exceptions.items()
    }


def _derive_available_date_range(
    *,
    calendars_by_service_id: dict[str, ServiceCalendar],
    exceptions_by_service_id: dict[str, tuple[CalendarDateException, ...]],
) -> tuple[date, date] | None:
    dates: list[date] = []
    for calendar in calendars_by_service_id.values():
        dates.extend((calendar.start_date, calendar.end_date))
    for exceptions in exceptions_by_service_id.values():
        dates.extend(exception.date for exception in exceptions)

    if not dates:
        return None

    return min(dates), max(dates)


def _read_rows(
    source: GtfsSource,
    file_name: str,
    *,
    required_columns: set[str],
) -> Iterator[tuple[int, dict[str, str]]]:
    header = source.read_header(file_name)
    missing_columns = sorted(required_columns.difference(header))
    if missing_columns:
        missing = ", ".join(missing_columns)
        raise ServiceCalendarError(f"GTFS file '{file_name}' is missing required columns: {missing}")

    with source.open_text(file_name) as handle:
        reader = csv.DictReader(handle)
        for row_number, raw_row in enumerate(reader, start=2):
            if raw_row is None:
                continue
            if None in raw_row:
                raise ServiceCalendarError(
                    f"GTFS file '{file_name}' has malformed row {row_number}: column count does not match the header"
                )

            normalized_row = {key: (value or "").strip() for key, value in raw_row.items()}
            if not any(normalized_row.values()):
                continue

            yield row_number, normalized_row


def _get_required_text(row: dict[str, str], file_name: str, row_number: int, field_name: str) -> str:
    value = row.get(field_name, "")
    if value == "":
        raise ServiceCalendarError(
            f"GTFS file '{file_name}' is missing required value for '{field_name}' on row {row_number}"
        )
    return value


def _parse_gtfs_flag(value: str, file_name: str, row_number: int, field_name: str) -> bool:
    if value == "1":
        return True
    if value == "0":
        return False
    raise ServiceCalendarError(
        f"GTFS file '{file_name}' has invalid flag '{value}' for '{field_name}' on row {row_number}"
    )


def _parse_gtfs_date(value: str, file_name: str, row_number: int, field_name: str) -> date:
    try:
        return datetime.strptime(value, GTFS_DATE_FORMAT).date()
    except ValueError as exc:
        raise ServiceCalendarError(
            f"GTFS file '{file_name}' has invalid date '{value}' for '{field_name}' on row {row_number}"
        ) from exc


def _parse_exception_type(value: str, *, row_number: int) -> CalendarDateExceptionType:
    try:
        return CalendarDateExceptionType(int(value))
    except (TypeError, ValueError) as exc:
        raise ServiceCalendarError(
            f"GTFS file 'calendar_dates.txt' has invalid exception_type '{value}' on row {row_number}"
        ) from exc