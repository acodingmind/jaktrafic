from __future__ import annotations

from datetime import date, datetime, timedelta

from app.logic.gtfs_loader import GtfsSchedule
from app.models.entities import Departure


def list_departures(
    *,
    schedule: GtfsSchedule,
    stop_id: str,
    travel_date: date,
    active_service_ids: tuple[str, ...],
) -> tuple[Departure, ...]:
    if stop_id not in schedule.stop_times_by_stop_id:
        return ()

    active_service_ids_set = set(active_service_ids)
    departures: list[Departure] = []
    for stop_time in schedule.stop_times_by_stop_id.get(stop_id, ()):
        trip = schedule.trips_by_id.get(stop_time.trip_id)
        if trip is None or trip.service_id not in active_service_ids_set:
            continue

        departures.append(
            Departure(
                stop_id=stop_id,
                trip_id=trip.trip_id,
                route_id=trip.route_id,
                headsign=trip.trip_headsign,
                scheduled_departure=_parse_gtfs_datetime(stop_time.departure_time, travel_date),
            )
        )

    departures.sort(key=lambda item: (item.scheduled_departure, item.route_id, item.trip_id))
    return tuple(departures)


def _parse_gtfs_datetime(gtfs_time: str, travel_date: date) -> datetime:
    hours_text, minutes_text, seconds_text = gtfs_time.split(":")
    midnight = datetime.combine(travel_date, datetime.min.time())
    return midnight + timedelta(
        hours=int(hours_text),
        minutes=int(minutes_text),
        seconds=int(seconds_text),
    )