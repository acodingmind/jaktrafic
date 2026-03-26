from __future__ import annotations

from datetime import date, datetime
from enum import Enum
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


GTFS_TIME_PATTERN = re.compile(r"^(?P<hours>\d+):(?P<minutes>[0-5]\d):(?P<seconds>[0-5]\d)$")


class FeedStatusState(str, Enum):
    HEALTHY = "healthy"
    WARNING = "warning"


class CalendarDateExceptionType(int, Enum):
    ADDED = 1
    REMOVED = 2


class EntityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Stop(EntityModel):
    stop_id: str = Field(min_length=1)
    stop_name: str = Field(min_length=1)
    stop_lat: float = Field(ge=-90, le=90)
    stop_lon: float = Field(ge=-180, le=180)
    parent_station: str | None = None


class RouteLine(EntityModel):
    route_id: str = Field(min_length=1)
    route_short_name: str | None = None
    route_long_name: str | None = None
    route_type: int
    agency_id: str | None = None


class Trip(EntityModel):
    trip_id: str = Field(min_length=1)
    route_id: str = Field(min_length=1)
    service_id: str = Field(min_length=1)
    trip_headsign: str | None = None


class StopTime(EntityModel):
    trip_id: str = Field(min_length=1)
    arrival_time: str
    departure_time: str
    stop_id: str = Field(min_length=1)
    stop_sequence: int = Field(ge=1)

    @field_validator("arrival_time", "departure_time")
    @classmethod
    def validate_gtfs_time(cls, value: str) -> str:
        if not GTFS_TIME_PATTERN.fullmatch(value):
            raise ValueError("must use GTFS HH:MM:SS format")
        return value


class CalendarDateException(EntityModel):
    service_id: str = Field(min_length=1)
    date: date
    exception_type: CalendarDateExceptionType


class ServiceCalendar(EntityModel):
    service_id: str = Field(min_length=1)
    start_date: date
    end_date: date
    monday: bool = False
    tuesday: bool = False
    wednesday: bool = False
    thursday: bool = False
    friday: bool = False
    saturday: bool = False
    sunday: bool = False
    exceptions: tuple[CalendarDateException, ...] = ()

    @model_validator(mode="after")
    def validate_date_range(self) -> ServiceCalendar:
        if self.start_date > self.end_date:
            raise ValueError("start_date must be on or before end_date")
        return self


class GtfsFeedWindow(EntityModel):
    feed_start_date: date | None = None
    feed_end_date: date | None = None
    feed_publisher_name: str | None = None
    feed_version: str | None = None

    @model_validator(mode="after")
    def validate_feed_window(self) -> GtfsFeedWindow:
        if self.feed_start_date and self.feed_end_date and self.feed_start_date > self.feed_end_date:
            raise ValueError("feed_start_date must be on or before feed_end_date")
        return self


class Leg(EntityModel):
    route_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)
    board_stop_id: str = Field(min_length=1)
    alight_stop_id: str = Field(min_length=1)
    board_time: datetime
    alight_time: datetime
    headsign: str | None = None

    @model_validator(mode="after")
    def validate_leg_times(self) -> Leg:
        if self.alight_time <= self.board_time:
            raise ValueError("alight_time must be later than board_time")
        return self


class Journey(EntityModel):
    journey_id: str = Field(min_length=1)
    origin_stop_id: str = Field(min_length=1)
    destination_stop_id: str = Field(min_length=1)
    departure_datetime: datetime
    arrival_datetime: datetime
    duration_minutes: int = Field(ge=0)
    transfer_count: int = Field(ge=0)
    legs: tuple[Leg, ...] = ()
    freshness_warning: bool = False

    @model_validator(mode="after")
    def validate_journey(self) -> Journey:
        if self.origin_stop_id == self.destination_stop_id:
            raise ValueError("destination_stop_id must differ from origin_stop_id")
        if self.arrival_datetime < self.departure_datetime:
            raise ValueError("arrival_datetime must be on or after departure_datetime")
        if self.transfer_count != max(len(self.legs) - 1, 0):
            raise ValueError("transfer_count must equal the number of transfers implied by legs")
        return self


class Departure(EntityModel):
    stop_id: str = Field(min_length=1)
    trip_id: str = Field(min_length=1)
    route_id: str = Field(min_length=1)
    headsign: str | None = None
    scheduled_departure: datetime


class StopSearchResult(EntityModel):
    stop_id: str = Field(min_length=1)
    stop_name: str = Field(min_length=1)
    locality: str | None = None


class FeedStatus(EntityModel):
    state: FeedStatusState
    message: str = Field(min_length=1)
    feed_start_date: date | None = None
    feed_end_date: date | None = None


__all__ = [
    "CalendarDateException",
    "CalendarDateExceptionType",
    "Departure",
    "EntityModel",
    "FeedStatus",
    "FeedStatusState",
    "GtfsFeedWindow",
    "Journey",
    "Leg",
    "RouteLine",
    "ServiceCalendar",
    "Stop",
    "StopSearchResult",
    "StopTime",
    "Trip",
]