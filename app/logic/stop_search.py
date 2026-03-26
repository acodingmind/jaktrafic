from __future__ import annotations

from app.logic.gtfs_loader import GtfsSchedule
from app.models.entities import StopSearchResult


def search_stops(
    schedule: GtfsSchedule,
    query: str,
    *,
    limit: int = 10,
) -> tuple[StopSearchResult, ...]:
    normalized_query = query.strip().casefold()
    if not normalized_query or limit <= 0:
        return ()

    ranked_stops: list[tuple[tuple[int, str, str], StopSearchResult]] = []
    for stop in schedule.stops_by_id.values():
        normalized_stop_name = stop.stop_name.casefold()
        if normalized_query not in normalized_stop_name:
            continue

        locality = _derive_locality(schedule, stop.parent_station)
        result = StopSearchResult(
            stop_id=stop.stop_id,
            stop_name=stop.stop_name,
            locality=locality,
        )
        ranked_stops.append((_rank_match(normalized_stop_name, normalized_query, stop.stop_name, stop.stop_id), result))

    ranked_stops.sort(key=lambda item: item[0])
    return tuple(result for _, result in ranked_stops[:limit])


def _rank_match(stop_name: str, query: str, display_name: str, stop_id: str) -> tuple[int, str, str]:
    if stop_name == query:
        priority = 0
    elif stop_name.startswith(query):
        priority = 1
    else:
        priority = 2
    return priority, display_name.casefold(), stop_id


def _derive_locality(schedule: GtfsSchedule, parent_station_id: str | None) -> str | None:
    if not parent_station_id:
        return None

    parent_station = schedule.stops_by_id.get(parent_station_id)
    if parent_station is None:
        return None
    return parent_station.stop_name