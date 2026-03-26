from __future__ import annotations

from collections import defaultdict
import csv
import io
from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, TextIO
from zipfile import BadZipFile, ZipFile

from pydantic import BaseModel, ValidationError

from app.models.entities import RouteLine, Stop, StopTime, Trip


REQUIRED_GTFS_FILES = {
    "stops.txt": ("stop_id", "stop_name", "stop_lat", "stop_lon"),
    "routes.txt": ("route_id", "route_type"),
    "trips.txt": ("route_id", "service_id", "trip_id"),
    "stop_times.txt": (
        "trip_id",
        "arrival_time",
        "departure_time",
        "stop_id",
        "stop_sequence",
    ),
}
OPTIONAL_GTFS_FILES = frozenset({"agency.txt", "calendar.txt", "calendar_dates.txt", "feed_info.txt", "shapes.txt"})


class GtfsSourceError(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class GtfsSchedule:
    source: GtfsSource
    stops_by_id: dict[str, Stop]
    routes_by_id: dict[str, RouteLine]
    trips_by_id: dict[str, Trip]
    trips_by_route_id: dict[str, tuple[Trip, ...]]
    stop_times_by_trip_id: dict[str, tuple[StopTime, ...]]
    stop_times_by_stop_id: dict[str, tuple[StopTime, ...]]

    @property
    def stop_count(self) -> int:
        return len(self.stops_by_id)

    @property
    def route_count(self) -> int:
        return len(self.routes_by_id)

    @property
    def trip_count(self) -> int:
        return len(self.trips_by_id)

    @property
    def stop_time_count(self) -> int:
        return sum(len(stop_times) for stop_times in self.stop_times_by_trip_id.values())


@dataclass(frozen=True, slots=True)
class GtfsSource:
    source_type: str
    source_path: Path
    file_map: dict[str, str]

    @property
    def available_files(self) -> tuple[str, ...]:
        return tuple(sorted(self.file_map))

    def has_file(self, file_name: str) -> bool:
        return file_name.lower() in self.file_map

    def get_entry_name(self, file_name: str) -> str:
        try:
            return self.file_map[file_name.lower()]
        except KeyError as exc:
            raise GtfsSourceError(f"GTFS file '{file_name}' is not available in {self.source_path}") from exc

    @contextmanager
    def open_text(self, file_name: str, *, encoding: str = "utf-8-sig", newline: str = "") -> Iterator[TextIO]:
        entry_name = self.get_entry_name(file_name)
        with ExitStack() as stack:
            if self.source_type == "directory":
                text_handle = stack.enter_context((self.source_path / entry_name).open("r", encoding=encoding, newline=newline))
            else:
                archive = stack.enter_context(ZipFile(self.source_path))
                binary_handle = stack.enter_context(archive.open(entry_name, "r"))
                text_handle = stack.enter_context(io.TextIOWrapper(binary_handle, encoding=encoding, newline=newline))
            yield text_handle

    def read_header(self, file_name: str) -> tuple[str, ...]:
        with self.open_text(file_name) as handle:
            reader = csv.reader(handle)
            header = next(reader, None)

        if header is None:
            raise GtfsSourceError(f"GTFS file '{file_name}' is empty")

        normalized_header = tuple(column.strip() for column in header if column is not None)
        if not any(normalized_header):
            raise GtfsSourceError(f"GTFS file '{file_name}' is missing a header row")

        return normalized_header

    def validate_required_headers(self) -> None:
        for file_name, required_columns in REQUIRED_GTFS_FILES.items():
            header = self.read_header(file_name)
            missing_columns = [column for column in required_columns if column not in header]
            if missing_columns:
                missing = ", ".join(missing_columns)
                raise GtfsSourceError(
                    f"GTFS file '{file_name}' is missing required columns: {missing}"
                )


def discover_gtfs_source(
    source_path: str | Path | None = None,
    archive_path: str | Path | None = None,
) -> GtfsSource:
    candidate_paths = _build_candidate_paths(source_path=source_path, archive_path=archive_path)
    if not candidate_paths:
        raise GtfsSourceError("No GTFS source paths were provided")

    errors: list[str] = []
    for candidate_path in candidate_paths:
        try:
            return _discover_candidate(candidate_path)
        except GtfsSourceError as exc:
            errors.append(str(exc))

    checked = ", ".join(str(path) for path in candidate_paths)
    details = "; ".join(errors)
    raise GtfsSourceError(f"Unable to discover a valid GTFS source from: {checked}. {details}")


def load_gtfs_schedule(
    source_path: str | Path | None = None,
    archive_path: str | Path | None = None,
    *,
    source: GtfsSource | None = None,
) -> GtfsSchedule:
    gtfs_source = source or discover_gtfs_source(source_path=source_path, archive_path=archive_path)

    stops_by_id = _load_entities(gtfs_source, "stops.txt", Stop, unique_key="stop_id")
    routes_by_id = _load_entities(gtfs_source, "routes.txt", RouteLine, unique_key="route_id")
    trips_by_id = _load_entities(gtfs_source, "trips.txt", Trip, unique_key="trip_id")
    stop_times = _load_stop_times(gtfs_source, trips_by_id=trips_by_id, stops_by_id=stops_by_id)

    trips_by_route: dict[str, list[Trip]] = defaultdict(list)
    for trip in trips_by_id.values():
        if trip.route_id not in routes_by_id:
            raise GtfsSourceError(
                f"GTFS file 'trips.txt' references unknown route_id '{trip.route_id}' for trip '{trip.trip_id}'"
            )
        trips_by_route[trip.route_id].append(trip)

    stop_times_by_trip: dict[str, list[StopTime]] = defaultdict(list)
    stop_times_by_stop: dict[str, list[StopTime]] = defaultdict(list)
    for stop_time in stop_times:
        stop_times_by_trip[stop_time.trip_id].append(stop_time)
        stop_times_by_stop[stop_time.stop_id].append(stop_time)

    sorted_stop_times_by_trip = {
        trip_id: tuple(sorted(times, key=lambda item: item.stop_sequence))
        for trip_id, times in stop_times_by_trip.items()
    }
    _validate_trip_stop_sequences(sorted_stop_times_by_trip)

    sorted_stop_times_by_stop = {
        stop_id: tuple(
            sorted(
                times,
                key=lambda item: (_gtfs_time_sort_key(item.departure_time), item.trip_id, item.stop_sequence),
            )
        )
        for stop_id, times in stop_times_by_stop.items()
    }

    sorted_trips_by_route = {
        route_id: tuple(sorted(trips, key=lambda item: item.trip_id))
        for route_id, trips in trips_by_route.items()
    }

    return GtfsSchedule(
        source=gtfs_source,
        stops_by_id=stops_by_id,
        routes_by_id=routes_by_id,
        trips_by_id=trips_by_id,
        trips_by_route_id=sorted_trips_by_route,
        stop_times_by_trip_id=sorted_stop_times_by_trip,
        stop_times_by_stop_id=sorted_stop_times_by_stop,
    )


def _build_candidate_paths(
    *,
    source_path: str | Path | None,
    archive_path: str | Path | None,
) -> list[Path]:
    candidates: list[Path] = []

    if archive_path is not None:
        _append_candidate(candidates, Path(archive_path))

    if source_path is not None:
        source_candidate = Path(source_path)
        _append_candidate(candidates, source_candidate)
        if source_candidate.is_dir():
            for zip_candidate in sorted(source_candidate.glob("*.zip")):
                _append_candidate(candidates, zip_candidate)

    return candidates


def _append_candidate(candidates: list[Path], candidate: Path) -> None:
    resolved_candidate = candidate.resolve()
    if resolved_candidate not in candidates:
        candidates.append(resolved_candidate)


def _discover_candidate(candidate_path: Path) -> GtfsSource:
    if not candidate_path.exists():
        raise GtfsSourceError(f"GTFS source '{candidate_path}' does not exist")

    if candidate_path.is_dir():
        return _discover_directory_source(candidate_path)

    if candidate_path.is_file() and candidate_path.suffix.lower() == ".zip":
        return _discover_zip_source(candidate_path)

    raise GtfsSourceError(
        f"GTFS source '{candidate_path}' must be a directory of .txt files or a .zip archive"
    )


def _discover_directory_source(directory_path: Path) -> GtfsSource:
    file_map = _collect_directory_entries(directory_path)
    _validate_required_files(directory_path, file_map)
    source = GtfsSource(source_type="directory", source_path=directory_path, file_map=file_map)
    source.validate_required_headers()
    return source


def _discover_zip_source(archive_path: Path) -> GtfsSource:
    try:
        with ZipFile(archive_path) as archive:
            file_map = _collect_archive_entries(archive)
    except BadZipFile as exc:
        raise GtfsSourceError(f"GTFS archive '{archive_path}' is not a valid zip file") from exc

    _validate_required_files(archive_path, file_map)
    source = GtfsSource(source_type="zip", source_path=archive_path, file_map=file_map)
    source.validate_required_headers()
    return source


def _collect_directory_entries(directory_path: Path) -> dict[str, str]:
    file_map: dict[str, str] = {}
    for file_path in sorted(directory_path.rglob("*.txt")):
        if not file_path.is_file():
            continue

        key = file_path.name.lower()
        relative_path = file_path.relative_to(directory_path).as_posix()
        _store_entry(file_map, key, relative_path, directory_path)

    return file_map


def _collect_archive_entries(archive: ZipFile) -> dict[str, str]:
    file_map: dict[str, str] = {}
    for entry_name in sorted(archive.namelist()):
        if entry_name.endswith("/"):
            continue

        if Path(entry_name).suffix.lower() != ".txt":
            continue

        key = Path(entry_name).name.lower()
        _store_entry(file_map, key, entry_name, Path(archive.filename or "<archive>"))

    return file_map


def _store_entry(file_map: dict[str, str], key: str, entry_name: str, source_path: Path) -> None:
    existing_entry = file_map.get(key)
    if existing_entry is not None and existing_entry != entry_name:
        raise GtfsSourceError(
            f"GTFS source '{source_path}' contains multiple entries for '{key}': "
            f"'{existing_entry}' and '{entry_name}'"
        )

    file_map[key] = entry_name


def _validate_required_files(source_path: Path, file_map: dict[str, str]) -> None:
    missing_files = [file_name for file_name in REQUIRED_GTFS_FILES if file_name not in file_map]
    if missing_files:
        missing = ", ".join(missing_files)
        raise GtfsSourceError(f"GTFS source '{source_path}' is missing required files: {missing}")


def _load_entities(
    source: GtfsSource,
    file_name: str,
    model_type: type[BaseModel],
    *,
    unique_key: str,
) -> dict[str, Any]:
    entities: dict[str, Any] = {}
    for row_number, row in _read_rows(source, file_name):
        entity = _build_model(file_name, row_number, row, model_type)
        entity_key = getattr(entity, unique_key)
        if entity_key in entities:
            raise GtfsSourceError(
                f"GTFS file '{file_name}' contains duplicate {unique_key} '{entity_key}' on row {row_number}"
            )
        entities[entity_key] = entity

    if not entities:
        raise GtfsSourceError(f"GTFS file '{file_name}' contains no data rows")

    return entities


def _load_stop_times(
    source: GtfsSource,
    *,
    trips_by_id: dict[str, Trip],
    stops_by_id: dict[str, Stop],
) -> list[StopTime]:
    stop_times: list[StopTime] = []
    for row_number, row in _read_rows(source, "stop_times.txt"):
        stop_time = _build_model("stop_times.txt", row_number, row, StopTime)
        if stop_time.trip_id not in trips_by_id:
            raise GtfsSourceError(
                f"GTFS file 'stop_times.txt' references unknown trip_id '{stop_time.trip_id}' on row {row_number}"
            )
        if stop_time.stop_id not in stops_by_id:
            raise GtfsSourceError(
                f"GTFS file 'stop_times.txt' references unknown stop_id '{stop_time.stop_id}' on row {row_number}"
            )
        stop_times.append(stop_time)

    if not stop_times:
        raise GtfsSourceError("GTFS file 'stop_times.txt' contains no data rows")

    return stop_times


def _read_rows(source: GtfsSource, file_name: str) -> Iterator[tuple[int, dict[str, str]]]:
    with source.open_text(file_name) as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise GtfsSourceError(f"GTFS file '{file_name}' is missing a header row")

        for row_number, raw_row in enumerate(reader, start=2):
            if raw_row is None:
                continue

            if None in raw_row:
                raise GtfsSourceError(
                    f"GTFS file '{file_name}' has malformed row {row_number}: column count does not match the header"
                )

            normalized_row = {key: (value or "").strip() for key, value in raw_row.items()}
            if not any(normalized_row.values()):
                continue

            yield row_number, normalized_row


def _build_model(file_name: str, row_number: int, row: dict[str, str], model_type: type[BaseModel]) -> Any:
    payload: dict[str, Any] = {}
    for field_name in model_type.model_fields:
        if field_name not in row:
            continue

        value = row[field_name]
        if value == "" and _field_allows_none(model_type, field_name):
            payload[field_name] = None
        else:
            payload[field_name] = value

    try:
        return model_type.model_validate(payload)
    except ValidationError as exc:
        raise GtfsSourceError(
            f"GTFS file '{file_name}' contains invalid data on row {row_number}: {exc}"
        ) from exc


def _field_allows_none(model_type: type[BaseModel], field_name: str) -> bool:
    field_info = model_type.model_fields[field_name]
    return not field_info.is_required()


def _validate_trip_stop_sequences(stop_times_by_trip: dict[str, tuple[StopTime, ...]]) -> None:
    for trip_id, stop_times in stop_times_by_trip.items():
        previous_sequence = None
        for stop_time in stop_times:
            if previous_sequence is not None and stop_time.stop_sequence <= previous_sequence:
                raise GtfsSourceError(
                    f"GTFS file 'stop_times.txt' contains non-increasing stop_sequence for trip '{trip_id}'"
                )
            previous_sequence = stop_time.stop_sequence


def _gtfs_time_sort_key(value: str) -> tuple[int, int, int]:
    hours_text, minutes_text, seconds_text = value.split(":", maxsplit=2)
    return int(hours_text), int(minutes_text), int(seconds_text)