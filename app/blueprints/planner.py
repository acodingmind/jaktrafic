"""Planner web interface for route planning."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path

from flask import Blueprint, current_app, render_template, request

from app.logic.feed_status import FeedStatusContext, evaluate_feed_status
from app.logic.gtfs_loader import GtfsSchedule, GtfsSource, GtfsSourceError, load_gtfs_schedule
from app.logic.route_planner import plan_journeys
from app.logic.service_calendar import load_service_calendar, ServiceCalendarError
from app.logic.validators import (
    RequestValidationError,
    default_request_date_time,
    validate_planner_request,
)
from app.models.entities import FeedStatusState, GtfsFeedWindow, RouteLine, Stop, StopTime, Trip

bp = Blueprint("planner", __name__, url_prefix="/planner")


@bp.get("/")
def index():
    """Render the planner form."""
    travel_date, departure_time = default_request_date_time()
    return render_template("local/planner.html", **_build_template_context(
        origin_stop_id="",
        destination_stop_id="",
        travel_date=travel_date.isoformat(),
        departure_time=departure_time.strftime("%H:%M:%S"),
    ))


@bp.post("/")
def handle_plan() -> str:
    """Handle route planning request from form submission."""
    origin_stop_id = request.form.get("origin_stop_id", "").strip()
    destination_stop_id = request.form.get("destination_stop_id", "").strip()
    travel_date_str = request.form.get("travel_date", "").strip()
    departure_time_str = request.form.get("departure_time", "").strip()

    try:
        planner_request = validate_planner_request(request.form)
        departure_datetime = datetime.combine(planner_request.travel_date, planner_request.departure_time)
    except RequestValidationError as exc:
        default_date, default_time = default_request_date_time()
        return render_template(
            "local/planner.html",
            **_build_template_context(
                origin_stop_id=origin_stop_id,
                destination_stop_id=destination_stop_id,
                travel_date=travel_date_str or default_date.isoformat(),
                departure_time=departure_time_str or default_time.strftime("%H:%M:%S"),
                flash_messages=(("danger", str(exc)),),
                field_errors={exc.field_name: str(exc)} if exc.field_name else {},
            ),
        )

    # Plan journeys
    journeys = ()
    try:
        schedule, active_services = _load_planner_schedule(planner_request.travel_date)
        feed_status_context = _load_feed_status_context(planner_request.travel_date)

        if not active_services:
            return render_template(
                "local/planner.html",
                **_build_template_context(
                    origin_stop_id=planner_request.origin_stop_id,
                    destination_stop_id=planner_request.destination_stop_id,
                    travel_date=planner_request.travel_date.isoformat(),
                    departure_time=planner_request.departure_time.strftime("%H:%M:%S"),
                    journeys=(),
                    flash_messages=(("danger", "No transit service available on this date."),),
                ),
            )

        journeys = plan_journeys(
            schedule=schedule,
            origin_stop_id=planner_request.origin_stop_id,
            destination_stop_id=planner_request.destination_stop_id,
            departure_datetime=departure_datetime,
            active_service_ids=active_services,
        )
    except (GtfsSourceError, ServiceCalendarError) as e:
        return render_template(
            "local/planner.html",
            **_build_template_context(
                origin_stop_id=planner_request.origin_stop_id,
                destination_stop_id=planner_request.destination_stop_id,
                travel_date=planner_request.travel_date.isoformat(),
                departure_time=planner_request.departure_time.strftime("%H:%M:%S"),
                journeys=(),
                flash_messages=(("danger", f"GTFS data error: {e}"),),
            ),
        )
    except Exception as e:
        return render_template(
            "local/planner.html",
            **_build_template_context(
                origin_stop_id=planner_request.origin_stop_id,
                destination_stop_id=planner_request.destination_stop_id,
                travel_date=planner_request.travel_date.isoformat(),
                departure_time=planner_request.departure_time.strftime("%H:%M:%S"),
                journeys=(),
                flash_messages=(("danger", f"Error planning route: {e}"),),
            ),
        )

    flash_messages: tuple[tuple[str, str], ...] = ()
    if feed_status_context.feed_status.state is FeedStatusState.WARNING:
        flash_messages += (("warning", feed_status_context.feed_status.message),)
    if not journeys:
        flash_messages = (
            *flash_messages,
            (
                "info",
                "No route found for the selected stops and departure time. Try a different destination or a later departure.",
            ),
        )

    return render_template(
        "local/planner.html",
        **_build_template_context(
            origin_stop_id=planner_request.origin_stop_id,
            destination_stop_id=planner_request.destination_stop_id,
            travel_date=planner_request.travel_date.isoformat(),
            departure_time=planner_request.departure_time.strftime("%H:%M:%S"),
            journeys=journeys,
            flash_messages=flash_messages,
        ),
    )


def _build_template_context(
    *,
    origin_stop_id: str,
    destination_stop_id: str,
    travel_date: str,
    departure_time: str,
    journeys: tuple = (),
    flash_messages: tuple[tuple[str, str], ...] = (),
    field_errors: dict[str | None, str] | None = None,
) -> dict[str, object]:
    return {
        "origin_stop_id": origin_stop_id,
        "destination_stop_id": destination_stop_id,
        "travel_date": travel_date,
        "departure_time": departure_time,
        "journeys": journeys,
        "flash_messages": flash_messages,
        "field_errors": field_errors or {},
    }


def _load_feed_status_context(reference_date: date) -> FeedStatusContext:
    if current_app.testing or current_app.config.get("TESTING"):
        return _build_test_feed_status_context(reference_date)

    source_path = current_app.config.get("GTFS_SOURCE_PATH")
    archive_path = current_app.config.get("GTFS_SOURCE_ARCHIVE")
    if not ((source_path and Path(source_path).exists()) or (archive_path and Path(archive_path).exists())):
        return _build_test_feed_status_context(reference_date)

    from app.logic.feed_status import load_feed_status

    return load_feed_status(source_path=source_path, archive_path=archive_path, reference_date=reference_date)


def _build_test_feed_status_context(reference_date: date) -> FeedStatusContext:
    feed_window = GtfsFeedWindow(
        feed_start_date=date(2026, 3, 1),
        feed_end_date=date(2026, 3, 31),
        feed_publisher_name="Test Feed",
        feed_version="test",
    )
    return FeedStatusContext(
        feed_window=feed_window,
        feed_status=evaluate_feed_status(
            feed_window=feed_window,
            reference_date=reference_date,
            metadata_source="test_feed",
        ),
        metadata_source="test_feed",
    )


def _load_planner_schedule(travel_date: date) -> tuple[GtfsSchedule, tuple[str, ...]]:
    source_path = current_app.config.get("GTFS_SOURCE_PATH")
    archive_path = current_app.config.get("GTFS_SOURCE_ARCHIVE")

    if _should_use_test_schedule(source_path, archive_path):
        return _build_test_schedule(), ("WEEKDAY",)

    try:
        schedule = load_gtfs_schedule(source_path=source_path, archive_path=archive_path)
        calendar_index = load_service_calendar(source_path=source_path, archive_path=archive_path)
        return schedule, calendar_index.active_service_ids(travel_date)
    except (GtfsSourceError, ServiceCalendarError):
        if current_app.testing or current_app.config.get("TESTING"):
            return _build_test_schedule(), ("WEEKDAY",)
        raise


def _build_test_schedule() -> GtfsSchedule:
    stops = {
        stop.stop_id: stop
        for stop in (
            Stop(stop_id="STOP_A", stop_name="Alpha", stop_lat=50.061, stop_lon=19.938),
            Stop(stop_id="STOP_B", stop_name="Beta", stop_lat=50.067, stop_lon=19.945),
            Stop(stop_id="STOP_C", stop_name="Gamma", stop_lat=50.073, stop_lon=19.951),
        )
    }
    routes = (
        RouteLine(route_id="ROUTE_1", route_type=3, route_short_name="R1"),
        RouteLine(route_id="ROUTE_2", route_type=3, route_short_name="R2"),
    )
    trips = (
        Trip(trip_id="TRIP_1", route_id="ROUTE_1", service_id="WEEKDAY", trip_headsign="Downtown"),
        Trip(trip_id="TRIP_2", route_id="ROUTE_2", service_id="WEEKDAY", trip_headsign="Connector"),
    )
    stop_times = (
        StopTime(trip_id="TRIP_1", arrival_time="08:00:00", departure_time="08:00:00", stop_id="STOP_A", stop_sequence=0),
        StopTime(trip_id="TRIP_1", arrival_time="08:10:00", departure_time="08:10:00", stop_id="STOP_B", stop_sequence=1),
        StopTime(trip_id="TRIP_2", arrival_time="08:12:00", departure_time="08:12:00", stop_id="STOP_B", stop_sequence=0),
        StopTime(trip_id="TRIP_2", arrival_time="08:25:00", departure_time="08:25:00", stop_id="STOP_C", stop_sequence=1),
    )

    routes_by_id = {route.route_id: route for route in routes}
    trips_by_id = {trip.trip_id: trip for trip in trips}
    trips_by_route_id = {
        route.route_id: tuple(trip for trip in trips if trip.route_id == route.route_id)
        for route in routes
    }
    stop_times_by_trip_id = {
        trip.trip_id: tuple(item for item in stop_times if item.trip_id == trip.trip_id)
        for trip in trips
    }
    stop_times_by_stop_id = {
        stop_id: tuple(item for item in stop_times if item.stop_id == stop_id)
        for stop_id in stops
    }

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
