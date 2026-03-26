from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile

import pytest

from app.logic.gtfs_loader import GtfsSourceError, discover_gtfs_source, load_gtfs_schedule


MINIMAL_GTFS_FILES = {
    "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\nSTOP_A,Alpha,50.061,19.938\nSTOP_B,Beta,50.067,19.945\n",
    "routes.txt": "route_id,route_type\nROUTE_1,3\n",
    "trips.txt": "route_id,service_id,trip_id\nROUTE_1,WEEKDAY,TRIP_1\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\nTRIP_1,08:00:00,08:00:00,STOP_A,0\nTRIP_1,08:10:00,08:10:00,STOP_B,1\n",
}


@pytest.mark.parametrize("source_kind", ["directory", "zip"])
def test_loader_supports_directory_and_zip_sources(tmp_path: Path, source_kind: str) -> None:
    data_dir = _write_gtfs_directory(tmp_path / "gtfs")

    if source_kind == "zip":
        archive_path = _write_gtfs_archive(tmp_path / "gtfs.zip", MINIMAL_GTFS_FILES)
        source = discover_gtfs_source(source_path=data_dir, archive_path=archive_path)
        schedule = load_gtfs_schedule(source_path=data_dir, archive_path=archive_path)
        assert source.source_type == "zip"
        assert source.source_path == archive_path.resolve()
    else:
        source = discover_gtfs_source(source_path=data_dir)
        schedule = load_gtfs_schedule(source_path=data_dir)
        assert source.source_type == "directory"
        assert source.source_path == data_dir.resolve()

    assert source.available_files == ("routes.txt", "stop_times.txt", "stops.txt", "trips.txt")
    assert schedule.stop_count == 2
    assert schedule.route_count == 1
    assert schedule.trip_count == 1
    assert schedule.stop_time_count == 2


def test_discover_gtfs_source_rejects_missing_required_header(tmp_path: Path) -> None:
    invalid_files = dict(MINIMAL_GTFS_FILES)
    invalid_files["stops.txt"] = "stop_id,stop_lat,stop_lon\nSTOP_A,50.061,19.938\n"
    data_dir = _write_gtfs_directory(tmp_path / "invalid-headers", invalid_files)

    with pytest.raises(GtfsSourceError, match="stops.txt'.*missing required columns: stop_name"):
        discover_gtfs_source(source_path=data_dir)


def test_load_gtfs_schedule_rejects_malformed_rows(tmp_path: Path) -> None:
    invalid_files = dict(MINIMAL_GTFS_FILES)
    invalid_files["stop_times.txt"] = (
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "TRIP_1,08:00:00,08:00:00,STOP_A,0\n"
        "TRIP_1,08:10:00,08:10:00,STOP_B,1,EXTRA\n"
    )
    data_dir = _write_gtfs_directory(tmp_path / "malformed-rows", invalid_files)

    with pytest.raises(GtfsSourceError, match="stop_times.txt'.*malformed row"):
        load_gtfs_schedule(source_path=data_dir)


def _write_gtfs_directory(base_path: Path, files: dict[str, str] | None = None) -> Path:
    base_path.mkdir(parents=True, exist_ok=True)
    for file_name, content in (files or MINIMAL_GTFS_FILES).items():
        (base_path / file_name).write_text(content, encoding="utf-8")
    return base_path


def _write_gtfs_archive(archive_path: Path, files: dict[str, str]) -> Path:
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(archive_path, "w") as archive:
        for file_name, content in files.items():
            archive.writestr(file_name, content)
    return archive_path