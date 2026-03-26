from __future__ import annotations

from datetime import date, datetime

import pytest

from app.logic.gtfs_loader import GtfsSchedule
from app.models.entities import Departure, RouteLine, Stop, StopTime, Trip


def test_list_departures_returns_sorted_departures_for_stop() -> None:
    list_departures = _load_list_departures()
    schedule = _build_schedule(
        routes=(RouteLine(route_id="R1", route_type=3, route_short_name="R1"),),
        trips=(
            Trip(trip_id="T2", route_id="R1", service_id="WK", trip_headsign="Northbound"),
            Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Downtown"),
        ),
        stop_times=(
            StopTime(trip_id="T2", arrival_time="08:20:00", departure_time="08:20:00", stop_id="STOP_A", stop_sequence=0),
            StopTime(trip_id="T1", arrival_time="08:05:00", departure_time="08:05:00", stop_id="STOP_A", stop_sequence=0),
        ),
    )

    departures = _run_list_departures(
        list_departures,
        schedule=schedule,
        stop_id="STOP_A",
        travel_date=date(2026, 3, 26),
        active_service_ids=("WK",),
    )

    assert [departure.trip_id for departure in departures] == ["T1", "T2"]
    assert departures[0].scheduled_departure == datetime(2026, 3, 26, 8, 5)


def test_list_departures_filters_out_inactive_services() -> None:
    list_departures = _load_list_departures()
    schedule = _build_schedule(
        routes=(RouteLine(route_id="R1", route_type=3, route_short_name="R1"),),
        trips=(
            Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Weekday"),
            Trip(trip_id="T2", route_id="R1", service_id="SAT", trip_headsign="Saturday"),
        ),
        stop_times=(
            StopTime(trip_id="T1", arrival_time="08:05:00", departure_time="08:05:00", stop_id="STOP_A", stop_sequence=0),
            StopTime(trip_id="T2", arrival_time="08:10:00", departure_time="08:10:00", stop_id="STOP_A", stop_sequence=0),
        ),
    )

    departures = _run_list_departures(
        list_departures,
        schedule=schedule,
        stop_id="STOP_A",
        travel_date=date(2026, 3, 26),
        active_service_ids=("WK",),
    )

    assert [departure.trip_id for departure in departures] == ["T1"]


def test_list_departures_returns_empty_when_stop_has_no_matches() -> None:
    list_departures = _load_list_departures()
    schedule = _build_schedule(
        routes=(RouteLine(route_id="R1", route_type=3, route_short_name="R1"),),
        trips=(Trip(trip_id="T1", route_id="R1", service_id="WK", trip_headsign="Weekday"),),
        stop_times=(
            StopTime(trip_id="T1", arrival_time="08:05:00", departure_time="08:05:00", stop_id="STOP_B", stop_sequence=0),
        ),
    )

    departures = _run_list_departures(
        list_departures,
        schedule=schedule,
        stop_id="STOP_A",
        travel_date=date(2026, 3, 26),
        active_service_ids=("WK",),
    )

    assert departures == ()


def _load_list_departures():
    try:
        from app.logic.departures_service import list_departures
    except ImportError as exc:
        pytest.xfail(f"departures service is not implemented yet: {exc}")

    return list_departures


def _run_list_departures(list_departures, **kwargs):
    try:
        return tuple(list_departures(**kwargs))
    except NotImplementedError as exc:
        pytest.xfail(f"departures service is not implemented yet: {exc}")


def _build_schedule(
    *,
    routes: tuple[RouteLine, ...],
    trips: tuple[Trip, ...],
    stop_times: tuple[StopTime, ...],
) -> GtfsSchedule:
    stops = {
        stop.stop_id: stop
        for stop in (
            Stop(stop_id="STOP_A", stop_name="Alpha", stop_lat=50.061, stop_lon=19.938),
            Stop(stop_id="STOP_B", stop_name="Beta", stop_lat=50.067, stop_lon=19.945),
            Stop(stop_id="STOP_C", stop_name="Gamma", stop_lat=50.073, stop_lon=19.951),
        )
    }
    routes_by_id = {route.route_id: route for route in routes}
    trips_by_id = {trip.trip_id: trip for trip in trips}
    trips_by_route_id = {route.route_id: tuple(trip for trip in trips if trip.route_id == route.route_id) for route in routes}
    stop_times_by_trip_id = {trip.trip_id: tuple(item for item in stop_times if item.trip_id == trip.trip_id) for trip in trips}
    stop_times_by_stop_id = {stop_id: tuple(item for item in stop_times if item.stop_id == stop_id) for stop_id in stops}

    return GtfsSchedule(
        source=None,  # type: ignore[arg-type]
        stops_by_id=stops,
        routes_by_id=routes_by_id,
        trips_by_id=trips_by_id,
        trips_by_route_id=trips_by_route_id,
        stop_times_by_trip_id=stop_times_by_trip_id,
        stop_times_by_stop_id=stop_times_by_stop_id,
    )