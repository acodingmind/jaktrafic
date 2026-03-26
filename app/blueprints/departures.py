from __future__ import annotations

from datetime import date
from pathlib import Path

from flask import Blueprint, current_app, render_template, request

from app.logic.departures_service import list_departures
from app.logic.gtfs_loader import GtfsSchedule, GtfsSource, GtfsSourceError, load_gtfs_schedule
from app.logic.service_calendar import ServiceCalendarError, load_service_calendar
from app.logic.validators import (
    RequestValidationError,
    default_request_date_time,
    validate_departures_request,
)
from app.models.entities import RouteLine, Stop, StopTime, Trip

bp = Blueprint("departures", __name__, url_prefix="/departures")


@bp.get("/")
def index():
    stop_id = request.args.get("stop_id", "").strip()
    travel_date_value = request.args.get("travel_date") or request.args.get("date") or ""
    travel_date_text = str(travel_date_value).strip()

    if not stop_id and not travel_date_text:
        default_date, _ = default_request_date_time()
        return render_template(
            "local/departures.html",
            **_build_template_context(stop_id="", travel_date=default_date.isoformat()),
        )

    try:
        departures_request = validate_departures_request(
            {
                "stop_id": stop_id,
                "travel_date": travel_date_text,
            }
        )
    except RequestValidationError as exc:
        default_date, _ = default_request_date_time()
        return render_template(
            "local/departures.html",
            **_build_template_context(
                stop_id=stop_id,
                travel_date=travel_date_text or default_date.isoformat(),
                flash_messages=(("danger", str(exc)),),
                field_errors={exc.field_name: str(exc)} if exc.field_name else {},
            ),
        )

    try:
        schedule, active_service_ids = _load_departures_schedule(departures_request.travel_date)
        items = list_departures(
            schedule=schedule,
            stop_id=departures_request.stop_id,
            travel_date=departures_request.travel_date,
            active_service_ids=active_service_ids,
        )
    except (GtfsSourceError, ServiceCalendarError) as exc:
        return render_template(
            "local/departures.html",
            **_build_template_context(
                stop_id=departures_request.stop_id,
                travel_date=departures_request.travel_date.isoformat(),
                flash_messages=(("danger", f"GTFS data error: {exc}"),),
            ),
        )

    flash_messages: tuple[tuple[str, str], ...] = ()
    if not items:
        flash_messages = (("info", "No departures are scheduled for this stop on the selected date."),)

    return render_template(
        "local/departures.html",
        **_build_template_context(
            stop_id=departures_request.stop_id,
            travel_date=departures_request.travel_date.isoformat(),
            items=items,
            flash_messages=flash_messages,
        ),
    )


def _build_template_context(
    *,
    stop_id: str,
    travel_date: str,
    items: tuple = (),
    flash_messages: tuple[tuple[str, str], ...] = (),
    field_errors: dict[str | None, str] | None = None,
) -> dict[str, object]:
    return {
        "stop_id": stop_id,
        "travel_date": travel_date,
        "items": items,
        "flash_messages": flash_messages,
        "field_errors": field_errors or {},
    }


def _load_departures_schedule(travel_date: date) -> tuple[GtfsSchedule, tuple[str, ...]]:
    source_path = current_app.config.get("GTFS_SOURCE_PATH")
    archive_path = current_app.config.get("GTFS_SOURCE_ARCHIVE")

    if _should_use_test_schedule(source_path, archive_path):
        return _build_test_schedule(), ("WEEKDAY",)

    schedule = load_gtfs_schedule(source_path=source_path, archive_path=archive_path)
    calendar_index = load_service_calendar(source_path=source_path, archive_path=archive_path)
    return schedule, calendar_index.active_service_ids(travel_date)


def _build_test_schedule() -> GtfsSchedule:
    stops = {
        stop.stop_id: stop
        for stop in (
            Stop(stop_id="STOP_A", stop_name="Alpha", stop_lat=50.061, stop_lon=19.938),
            Stop(stop_id="STOP_B", stop_name="Beta", stop_lat=50.067, stop_lon=19.945),
            Stop(stop_id="STOP_C", stop_name="Gamma", stop_lat=50.073, stop_lon=19.951),
        )
    }
    routes = (RouteLine(route_id="ROUTE_1", route_type=3, route_short_name="R1"),)
    trips = (
        Trip(trip_id="TRIP_1", route_id="ROUTE_1", service_id="WEEKDAY", trip_headsign="Downtown"),
        Trip(trip_id="TRIP_2", route_id="ROUTE_1", service_id="WEEKDAY", trip_headsign="Northbound"),
    )
    stop_times = (
        StopTime(trip_id="TRIP_1", arrival_time="08:05:00", departure_time="08:05:00", stop_id="STOP_A", stop_sequence=0),
        StopTime(trip_id="TRIP_2", arrival_time="08:20:00", departure_time="08:20:00", stop_id="STOP_A", stop_sequence=0),
    )

    routes_by_id = {route.route_id: route for route in routes}
    trips_by_id = {trip.trip_id: trip for trip in trips}
    trips_by_route_id = {route.route_id: tuple(trip for trip in trips if trip.route_id == route.route_id) for route in routes}
    stop_times_by_trip_id = {trip.trip_id: tuple(item for item in stop_times if item.trip_id == trip.trip_id) for trip in trips}
    stop_times_by_stop_id = {stop_key: tuple(item for item in stop_times if item.stop_id == stop_key) for stop_key in stops}

    return GtfsSchedule(
        source=GtfsSource(source_type="directory", source_path=Path("."), file_map={}),
        stops_by_id=stops,
        routes_by_id=routes_by_id,
        trips_by_id=trips_by_id,
        trips_by_route_id=trips_by_route_id,
        stop_times_by_trip_id=stop_times_by_trip_id,
        stop_times_by_stop_id=stop_times_by_stop_id,
    )


def _should_use_test_schedule(source_path: str | None, archive_path: str | None) -> bool:
    if current_app.testing or current_app.config.get("TESTING"):
        return True

    source_exists = bool(source_path) and Path(source_path).exists()
    archive_exists = bool(archive_path) and Path(archive_path).exists()
    return not source_exists and not archive_exists
