from __future__ import annotations

from datetime import date
from pathlib import Path
from zipfile import ZipFile

import pytest

from app.logic.feed_status import load_feed_status
from app.logic.gtfs_loader import GtfsSourceError, load_gtfs_schedule
from app.logic.service_calendar import ServiceCalendarError, load_service_calendar


BASE_GTFS_FILES = {
    "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\nSTOP_A,Alpha,50.061,19.938\nSTOP_B,Beta,50.067,19.945\n",
    "routes.txt": "route_id,route_type\nROUTE_1,3\n",
    "trips.txt": "route_id,service_id,trip_id\nROUTE_1,WEEKDAY,TRIP_1\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nTRIP_1,08:00:00,08:00:00,STOP_A,0\nTRIP_1,08:10:00,08:10:00,STOP_B,1\n",
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "WEEKDAY,1,1,1,1,1,0,0,20260301,20260331\n"
    ),
    "calendar_dates.txt": (
        "service_id,date,exception_type\n"
        "WEEKDAY,20260302,2\n"
        "WEEKDAY,20260308,1\n"
    ),
}


@pytest.mark.parametrize("source_kind", ["directory", "zip"])
def test_ingestion_switches_between_directory_and_zip(tmp_path: Path, source_kind: str) -> None:
    source_path, archive_path = _prepare_source(tmp_path, BASE_GTFS_FILES, source_kind)

    schedule = load_gtfs_schedule(source_path=source_path, archive_path=archive_path)
    calendar_index = load_service_calendar(source_path=source_path, archive_path=archive_path)
    feed_status = load_feed_status(
        source_path=source_path,
        archive_path=archive_path,
        reference_date=date(2026, 3, 10),
    )

    expected_source_type = "zip" if source_kind == "zip" else "directory"
    assert schedule.source.source_type == expected_source_type
    assert schedule.stop_count == 2
    assert calendar_index.active_service_ids(date(2026, 3, 10)) == ("WEEKDAY",)
    assert feed_status.feed_status.state.value == "healthy"


def test_ingestion_rejects_missing_required_fields(tmp_path: Path) -> None:
    invalid_files = dict(BASE_GTFS_FILES)
    invalid_files["trips.txt"] = "route_id,service_id\nROUTE_1,WEEKDAY\n"
    source_path, archive_path = _prepare_source(tmp_path, invalid_files, "directory")

    with pytest.raises(GtfsSourceError, match="trips.txt'.*missing required columns: trip_id"):
        load_gtfs_schedule(source_path=source_path, archive_path=archive_path)


def test_ingestion_rejects_malformed_stop_times_rows(tmp_path: Path) -> None:
    invalid_files = dict(BASE_GTFS_FILES)
    invalid_files["stop_times.txt"] = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "TRIP_1,08:00:00,08:00:00,STOP_A,0\n"
        "TRIP_1,08:10:00,08:10:00,STOP_B,1,EXTRA\n"
    )
    source_path, archive_path = _prepare_source(tmp_path, invalid_files, "zip")

    with pytest.raises(GtfsSourceError, match="stop_times.txt'.*malformed row"):
        load_gtfs_schedule(source_path=source_path, archive_path=archive_path)


def test_calendar_edge_cases_respect_removed_and_added_service_dates(tmp_path: Path) -> None:
    source_path, archive_path = _prepare_source(tmp_path, BASE_GTFS_FILES, "directory")

    calendar_index = load_service_calendar(source_path=source_path, archive_path=archive_path)
    expired_status = load_feed_status(
        source_path=source_path,
        archive_path=archive_path,
        reference_date=date(2026, 4, 5),
    )

    assert calendar_index.is_active("WEEKDAY", date(2026, 3, 2)) is False
    assert calendar_index.is_active("WEEKDAY", date(2026, 3, 8)) is True
    assert expired_status.feed_status.state.value == "warning"
    assert expired_status.feed_status.feed_end_date == date(2026, 3, 31)


def test_calendar_ingestion_rejects_missing_calendar_sources(tmp_path: Path) -> None:
    invalid_files = dict(BASE_GTFS_FILES)
    invalid_files.pop("calendar.txt")
    invalid_files.pop("calendar_dates.txt")
    source_path, archive_path = _prepare_source(tmp_path, invalid_files, "directory")

    with pytest.raises(ServiceCalendarError, match="must provide at least one of 'calendar.txt' or 'calendar_dates.txt'"):
        load_service_calendar(source_path=source_path, archive_path=archive_path)


def _prepare_source(tmp_path: Path, files: dict[str, str], source_kind: str) -> tuple[str, str | None]:
    data_dir = tmp_path / "gtfs"
    data_dir.mkdir(parents=True, exist_ok=True)
    for file_name, content in files.items():
        (data_dir / file_name).write_text(content, encoding="utf-8")

    if source_kind == "zip":
        archive_path = tmp_path / "gtfs.zip"
        with ZipFile(archive_path, "w") as archive:
            for file_name, content in files.items():
                archive.writestr(file_name, content)
        return str(data_dir), str(archive_path)

    return str(data_dir), None