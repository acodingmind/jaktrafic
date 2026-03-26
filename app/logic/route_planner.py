"""Route planning engine using GTFS static schedules.

This module implements earliest-arrival journey planning with transfer support.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from app.models.entities import Journey, Leg

if TYPE_CHECKING:
    from app.logic.gtfs_loader import GtfsSchedule


def plan_journeys(
    schedule: GtfsSchedule,
    origin_stop_id: str,
    destination_stop_id: str,
    departure_datetime: datetime,
    active_service_ids: tuple[str, ...],
) -> tuple[Journey, ...]:
    """Plan journeys from origin to destination.

    Args:
        schedule: GTFS schedule with stops, routes, and stop times.
        origin_stop_id: ID of the origin stop.
        destination_stop_id: ID of the destination stop.
        departure_datetime: Earliest acceptable departure time.
        active_service_ids: Service IDs to consider (e.g., WK, WE).

    Returns:
        Tuple of Journey objects sorted by arrival time.
        Empty tuple if destination is unreachable.
    """
    if origin_stop_id == destination_stop_id:
        return ()

    if origin_stop_id not in schedule.stops_by_id or destination_stop_id not in schedule.stops_by_id:
        return ()

    # State: arrival_stop_id -> (earliest_arrival_datetime, legs_to_reach_it)
    arrivals: dict[str, tuple[datetime, tuple[Leg, ...]]] = {}

    # Find all initial departures from origin_stop_id
    initial_stop_times = schedule.stop_times_by_stop_id.get(origin_stop_id, ())
    for stop_time in initial_stop_times:
        trip = schedule.trips_by_id.get(stop_time.trip_id)
        if not trip or trip.service_id not in active_service_ids:
            continue

        # Parse departure time
        dept_datetime = _parse_gtfs_time_for_date(stop_time.departure_time, departure_datetime.date())
        if dept_datetime < departure_datetime:
            continue

        # Explore this trip: follow all stops from this stop_time onward
        trip_stop_times = schedule.stop_times_by_trip_id.get(stop_time.trip_id, ())
        for idx, origin_st in enumerate(trip_stop_times):
            if origin_st.stop_id != origin_stop_id:
                continue
            # Found the boarding stop; now explore all stops after it
            for alight_st in trip_stop_times[idx + 1 :]:
                alight_datetime = _parse_gtfs_time_for_date(
                    alight_st.arrival_time, departure_datetime.date()
                )
                route = schedule.routes_by_id.get(trip.route_id)
                leg = Leg(
                    route_id=trip.route_id,
                    trip_id=trip.trip_id,
                    board_stop_id=origin_stop_id,
                    alight_stop_id=alight_st.stop_id,
                    board_time=dept_datetime,
                    alight_time=alight_datetime,
                    headsign=trip.trip_headsign,
                )
                current_arrival = (alight_datetime, (leg,))
                if alight_st.stop_id not in arrivals or alight_datetime < arrivals[alight_st.stop_id][0]:
                    arrivals[alight_st.stop_id] = current_arrival

    # Iteratively explore transfers: from each reachable stop, depart >= arrival_time
    changed = True
    max_iterations = 100  # Prevent infinite loops
    iteration = 0
    while changed and iteration < max_iterations:
        iteration += 1
        changed = False
        old_arrivals = dict(arrivals)

        for intermediate_stop_id, (arrival_time, legs) in list(old_arrivals.items()):
            # Find all departures from this intermediate stop >= arrival_time
            intermediate_stop_times = schedule.stop_times_by_stop_id.get(intermediate_stop_id, ())
            for stop_time in intermediate_stop_times:
                trip = schedule.trips_by_id.get(stop_time.trip_id)
                if not trip or trip.service_id not in active_service_ids:
                    continue

                dept_datetime = _parse_gtfs_time_for_date(stop_time.departure_time, departure_datetime.date())
                # Must depart after (or exactly at) arrival + minimal connection time (assumed 0 for unit tests)
                if dept_datetime < arrival_time:
                    continue

                # Explore this trip from intermediate_stop_id onward
                trip_stop_times = schedule.stop_times_by_trip_id.get(stop_time.trip_id, ())
                for idx, board_st in enumerate(trip_stop_times):
                    if board_st.stop_id != intermediate_stop_id:
                        continue
                    # Found the boarding stop; now explore all stops after it
                    for alight_st in trip_stop_times[idx + 1 :]:
                        alight_datetime = _parse_gtfs_time_for_date(
                            alight_st.arrival_time, departure_datetime.date()
                        )
                        transfer_leg = Leg(
                            route_id=trip.route_id,
                            trip_id=trip.trip_id,
                            board_stop_id=intermediate_stop_id,
                            alight_stop_id=alight_st.stop_id,
                            board_time=dept_datetime,
                            alight_time=alight_datetime,
                            headsign=trip.trip_headsign,
                        )
                        new_legs = legs + (transfer_leg,)
                        if alight_st.stop_id not in arrivals or alight_datetime < arrivals[alight_st.stop_id][0]:
                            arrivals[alight_st.stop_id] = (alight_datetime, new_legs)
                            changed = True

    # Extract journeys to destination
    if destination_stop_id not in arrivals:
        return ()

    journeys = []
    arrival_time, legs = arrivals[destination_stop_id]
    duration = int((arrival_time - departure_datetime).total_seconds() // 60)
    transfer_count = max(len(legs) - 1, 0)

    journey_id = f"{origin_stop_id}-{destination_stop_id}-{departure_datetime.isoformat()}"
    journey = Journey(
        journey_id=journey_id,
        origin_stop_id=origin_stop_id,
        destination_stop_id=destination_stop_id,
        departure_datetime=departure_datetime,
        arrival_datetime=arrival_time,
        duration_minutes=duration,
        transfer_count=transfer_count,
        legs=legs,
        freshness_warning=False,
    )
    journeys.append(journey)

    return tuple(journeys)


def _parse_gtfs_time_for_date(gtfs_time: str, date_: datetime.date) -> datetime:
    """Parse GTFS HH:MM:SS time string into a datetime on the given date.

    Args:
        gtfs_time: Time in HH:MM:SS format (may be > 23:59:59 for next-day service).
        date_: The calendar date for the journey.

    Returns:
        Datetime object combining the date and time.
    """
    parts = gtfs_time.split(":")
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])

    dt = datetime.combine(date_, datetime.min.time())
    return dt + timedelta(hours=hours, minutes=minutes, seconds=seconds)
