from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time
from typing import Mapping

from dateutil import parser


class RequestValidationError(ValueError):
    def __init__(self, message: str, *, field_name: str | None = None):
        super().__init__(message)
        self.field_name = field_name


@dataclass(frozen=True, slots=True)
class PlannerRequest:
    origin_stop_id: str
    destination_stop_id: str
    travel_date: date
    departure_time: time


@dataclass(frozen=True, slots=True)
class DeparturesRequest:
    stop_id: str
    travel_date: date


def require_text(value: str | None, *, field_name: str, label: str | None = None) -> str:
    normalized_value = (value or "").strip()
    if normalized_value == "":
        field_label = label or field_name.replace("_", " ")
        raise RequestValidationError(f"{field_label.capitalize()} is required.", field_name=field_name)
    return normalized_value


def validate_distinct_stop_ids(origin_stop_id: str, destination_stop_id: str) -> tuple[str, str]:
    origin = require_text(origin_stop_id, field_name="origin_stop_id", label="origin stop")
    destination = require_text(destination_stop_id, field_name="destination_stop_id", label="destination stop")
    if origin == destination:
        raise RequestValidationError(
            "Origin and destination must be different stops.",
            field_name="destination_stop_id",
        )
    return origin, destination


def parse_travel_date(value: str | date | datetime | None, *, field_name: str = "travel_date") -> date:
    if value is None:
        raise RequestValidationError("Travel date is required.", field_name=field_name)

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value

    normalized_value = require_text(str(value), field_name=field_name, label="travel date")
    try:
        return parser.isoparse(normalized_value).date()
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(
            "Travel date must use a valid ISO date format, for example 2026-03-26.",
            field_name=field_name,
        ) from exc


def parse_departure_time(value: str | time | datetime | None, *, field_name: str = "departure_time") -> time:
    if value is None:
        raise RequestValidationError("Departure time is required.", field_name=field_name)

    if isinstance(value, datetime):
        return value.time().replace(microsecond=0)
    if isinstance(value, time):
        return value.replace(microsecond=0)

    normalized_value = require_text(str(value), field_name=field_name, label="departure time")
    try:
        parsed = parser.parse(normalized_value)
    except (TypeError, ValueError) as exc:
        raise RequestValidationError(
            "Departure time must use a valid 24-hour or 12-hour time format.",
            field_name=field_name,
        ) from exc

    return parsed.time().replace(microsecond=0)


def parse_optional_travel_date(value: str | date | datetime | None) -> date | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return parse_travel_date(value)


def parse_optional_departure_time(value: str | time | datetime | None) -> time | None:
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    return parse_departure_time(value)


def validate_required_params(params: Mapping[str, object], required_fields: tuple[str, ...]) -> dict[str, str]:
    normalized_params: dict[str, str] = {}
    for field_name in required_fields:
        raw_value = params.get(field_name)
        normalized_params[field_name] = require_text(
            None if raw_value is None else str(raw_value),
            field_name=field_name,
        )
    return normalized_params


def validate_planner_request(params: Mapping[str, object]) -> PlannerRequest:
    normalized = validate_required_params(
        params,
        required_fields=("origin_stop_id", "destination_stop_id"),
    )
    origin_stop_id, destination_stop_id = validate_distinct_stop_ids(
        normalized["origin_stop_id"],
        normalized["destination_stop_id"],
    )
    travel_date = parse_travel_date(params.get("travel_date"))
    departure_time = parse_departure_time(params.get("departure_time"))
    return PlannerRequest(
        origin_stop_id=origin_stop_id,
        destination_stop_id=destination_stop_id,
        travel_date=travel_date,
        departure_time=departure_time,
    )


def validate_departures_request(params: Mapping[str, object]) -> DeparturesRequest:
    normalized = validate_required_params(params, required_fields=("stop_id",))
    travel_date = parse_travel_date(params.get("travel_date"))
    return DeparturesRequest(stop_id=normalized["stop_id"], travel_date=travel_date)


def default_request_date_time(now: datetime | None = None) -> tuple[date, time]:
    current = now or datetime.now()
    return current.date(), current.time().replace(microsecond=0)


__all__ = [
    "DeparturesRequest",
    "PlannerRequest",
    "RequestValidationError",
    "default_request_date_time",
    "parse_departure_time",
    "parse_optional_departure_time",
    "parse_optional_travel_date",
    "parse_travel_date",
    "require_text",
    "validate_departures_request",
    "validate_distinct_stop_ids",
    "validate_planner_request",
    "validate_required_params",
]