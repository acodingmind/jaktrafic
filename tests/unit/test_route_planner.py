from __future__ import annotations

from datetime import datetime

import pytest

from app.logic.gtfs_loader import GtfsSchedule
from app.models.entities import Leg, RouteLine, Stop, StopTime, Trip


def test_plan_journeys_prefers_earliest_arrival() -> None:
    plan_journeys = _load_plan_journeys()
    schedule = _build_schedule(
        routes=(
            RouteLine(route_id="R1", route_type=3, route_short_name="R1"),
            RouteLine(route_id="R2", route_type=3, route_short_name="R2"),
        ),
        trips=(
            Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Downtown"),
            Trip(trip_id="T2", route_id="R2", service_id="WK", trip_headsign="Express"),
        ),
        stop_times=(
            StopTime(trip_id="T1", arrival_time="08:00:00", departure_time="08:00:00", stop_id="A", stop_sequence=0),
            StopTime(trip_id="T1", arrival_time="08:35:00", departure_time="08:35:00", stop_id="C", stop_sequence=1),
            StopTime(trip_id="T2", arrival_time="08:05:00", departure_time="08:05:00", stop_id="A", stop_sequence=0),
            StopTime(trip_id="T2", arrival_time="08:20:00", departure_time="08:20:00", stop_id="C", stop_sequence=1),
        ),
    )

    journeys = _run_plan_journeys(
        plan_journeys,
        schedule=schedule,
        origin_stop_id="A",
        destination_stop_id="C",
        departure_datetime=datetime(2026, 3, 26, 8, 0),
        active_service_ids=("WK",),
    )

    assert journeys, "expected at least one journey option"
    assert journeys[0].arrival_datetime == datetime(2026, 3, 26, 8, 20)
    assert journeys[0].transfer_count == 0
    assert journeys[0].legs[0].trip_id == "T2"


def test_plan_journeys_builds_transfer_when_it_arrives_earlier() -> None:
    plan_journeys = _load_plan_journeys()
    schedule = _build_schedule(
        routes=(
            RouteLine(route_id="R1", route_type=3, route_short_name="R1"),
            RouteLine(route_id="R2", route_type=3, route_short_name="R2"),
            RouteLine(route_id="R3", route_type=3, route_short_name="R3"),
        ),
        trips=(
            Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Midtown"),
            Trip(trip_id="T2", route_id="R2", service_id="WK", trip_headsign="Central"),
            Trip(trip_id="T3", route_id="R3", service_id="WK", trip_headsign="Slow Direct"),
        ),
        stop_times=(
            StopTime(trip_id="T1", arrival_time="08:00:00", departure_time="08:00:00", stop_id="A", stop_sequence=0),
            StopTime(trip_id="T1", arrival_time="08:10:00", departure_time="08:10:00", stop_id="B", stop_sequence=1),
            StopTime(trip_id="T2", arrival_time="08:12:00", departure_time="08:12:00", stop_id="B", stop_sequence=0),
            StopTime(trip_id="T2", arrival_time="08:25:00", departure_time="08:25:00", stop_id="C", stop_sequence=1),
            StopTime(trip_id="T3", arrival_time="08:20:00", departure_time="08:20:00", stop_id="A", stop_sequence=0),
            StopTime(trip_id="T3", arrival_time="08:40:00", departure_time="08:40:00", stop_id="C", stop_sequence=1),
        ),
    )

    journeys = _run_plan_journeys(
        plan_journeys,
        schedule=schedule,
        origin_stop_id="A",
        destination_stop_id="C",
        departure_datetime=datetime(2026, 3, 26, 8, 0),
        active_service_ids=("WK",),
    )

    assert journeys, "expected at least one journey option"
    assert journeys[0].arrival_datetime == datetime(2026, 3, 26, 8, 25)
    assert journeys[0].transfer_count == 1
    assert [leg.trip_id for leg in journeys[0].legs] == ["T1", "T2"]


def test_plan_journeys_returns_no_options_when_destination_is_unreachable() -> None:
    plan_journeys = _load_plan_journeys()
    schedule = _build_schedule(
        routes=(RouteLine(route_id="R1", route_type=3, route_short_name="R1"),),
        trips=(Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Only Branch"),),
        stop_times=(
            StopTime(trip_id="T1", arrival_time="08:00:00", departure_time="08:00:00", stop_id="A", stop_sequence=0),
            StopTime(trip_id="T1", arrival_time="08:10:00", departure_time="08:10:00", stop_id="B", stop_sequence=1),
        ),
    )

    journeys = _run_plan_journeys(
        plan_journeys,
        schedule=schedule,
        origin_stop_id="A",
        destination_stop_id="C",
        departure_datetime=datetime(2026, 3, 26, 8, 0),
        active_service_ids=("WK",),
    )

    assert journeys == ()


def _load_plan_journeys():
    try:
        from app.logic.route_planner import plan_journeys
    except ImportError as exc:
        pytest.xfail(f"route planner engine is not implemented yet: {exc}")

    return plan_journeys


def _run_plan_journeys(plan_journeys, **kwargs):
    try:
        return tuple(plan_journeys(**kwargs))
    except NotImplementedError as exc:
        pytest.xfail(f"route planner engine is not implemented yet: {exc}")


def _build_schedule(
    *,
    routes: tuple[RouteLine, ...],
    trips: tuple[Trip, ...],
    stop_times: tuple[StopTime, ...],
) -> GtfsSchedule:
    stops = {
        stop.stop_id: stop
        for stop in (
            Stop(stop_id="A", stop_name="Alpha", stop_lat=50.061, stop_lon=19.938),
            Stop(stop_id="B", stop_name="Beta", stop_lat=50.067, stop_lon=19.945),
            Stop(stop_id="C", stop_name="Gamma", stop_lat=50.073, stop_lon=19.951),
        )
    }
    routes_by_id = {route.route_id: route for route in routes}
    trips_by_id = {trip.trip_id: trip for trip in trips}
    trips_by_route_id: dict[str, tuple[Trip, ...]] = {}
    for route in routes:
        trips_by_route_id[route.route_id] = tuple(trip for trip in trips if trip.route_id == route.route_id)

    stop_times_by_trip_id: dict[str, tuple[StopTime, ...]] = {}
    stop_times_by_stop_id: dict[str, tuple[StopTime, ...]] = {}
    for trip in trips:
        stop_times_by_trip_id[trip.trip_id] = tuple(item for item in stop_times if item.trip_id == trip.trip_id)
    for stop_id in stops:
        stop_times_by_stop_id[stop_id] = tuple(item for item in stop_times if item.stop_id == stop_id)

    return GtfsSchedule(
        source=None,  # type: ignore[arg-type]
        stops_by_id=stops,
        routes_by_id=routes_by_id,
        trips_by_id=trips_by_id,
        trips_by_route_id=trips_by_route_id,
        stop_times_by_trip_id=stop_times_by_trip_id,
        stop_times_by_stop_id=stop_times_by_stop_id,
    )