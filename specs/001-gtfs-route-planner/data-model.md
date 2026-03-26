# Data Model - JakTrafic GTFS Route Planner

## Entity: Stop
- Source: `stops.txt`
- Fields:
  - `stop_id` (string, required, unique)
  - `stop_name` (string, required)
  - `stop_lat` (float, required)
  - `stop_lon` (float, required)
  - `parent_station` (string, optional)
- Relationships:
  - One-to-many with `Departure` (a stop can have many departures)
  - Referenced by `Leg.board_stop_id` and `Leg.alight_stop_id`
- Validation rules:
  - `stop_name` must be non-empty
  - lat/lon must be valid geographic values

## Entity: RouteLine
- Source: `routes.txt`
- Fields:
  - `route_id` (string, required, unique)
  - `route_short_name` (string, optional)
  - `route_long_name` (string, optional)
  - `route_type` (int, required)
  - `agency_id` (string, optional)
- Relationships:
  - One-to-many with `Trip`

## Entity: Trip
- Source: `trips.txt`
- Fields:
  - `trip_id` (string, required, unique)
  - `route_id` (string, required, FK -> RouteLine)
  - `service_id` (string, required)
  - `trip_headsign` (string, optional)
- Relationships:
  - Many-to-one with `RouteLine`
  - One-to-many with `StopTime`

## Entity: StopTime
- Source: `stop_times.txt`
- Fields:
  - `trip_id` (string, required, FK -> Trip)
  - `arrival_time` (string HH:MM:SS, required)
  - `departure_time` (string HH:MM:SS, required)
  - `stop_id` (string, required, FK -> Stop)
  - `stop_sequence` (int, required)
- Relationships:
  - Many-to-one with `Trip`
  - Many-to-one with `Stop`
- Validation rules:
  - `stop_sequence` strictly increasing per `trip_id`

## Entity: ServiceCalendar
- Source: `calendar.txt`, `calendar_dates.txt`
- Fields:
  - `service_id` (string, required)
  - `start_date` (date, required)
  - `end_date` (date, required)
  - weekday flags (`monday`..`sunday`)
  - exceptions (add/remove per date)
- Relationships:
  - One-to-many with `Trip` via `service_id`
- Validation rules:
  - `start_date <= end_date`

## Entity: GtfsFeedWindow
- Source: `feed_info.txt`
- Fields:
  - `feed_start_date` (date, optional)
  - `feed_end_date` (date, optional)
  - `feed_publisher_name` (string, optional)
  - `feed_version` (string, optional)
- Validation rules:
  - if both dates exist, `feed_start_date <= feed_end_date`
- State transitions:
  - `healthy`: current date in feed range or no range provided
  - `warning`: current date outside range

## Entity: Journey
- Derived runtime entity
- Fields:
  - `journey_id` (string)
  - `origin_stop_id` (string)
  - `destination_stop_id` (string)
  - `departure_datetime` (datetime)
  - `arrival_datetime` (datetime)
  - `duration_minutes` (int)
  - `transfer_count` (int)
  - `legs` (list<Leg>)
  - `freshness_warning` (boolean)
- Validation rules:
  - destination must differ from origin
  - `arrival_datetime >= departure_datetime`

## Entity: Leg
- Derived runtime entity
- Fields:
  - `route_id` (string)
  - `trip_id` (string)
  - `board_stop_id` (string)
  - `alight_stop_id` (string)
  - `board_time` (datetime)
  - `alight_time` (datetime)
  - `headsign` (string, optional)
- Validation rules:
  - `alight_time > board_time`

## Entity: Departure
- Derived runtime entity
- Fields:
  - `stop_id` (string)
  - `trip_id` (string)
  - `route_id` (string)
  - `headsign` (string, optional)
  - `scheduled_departure` (datetime)
- Validation rules:
  - only services active on selected date are included

## Derived Aggregates
- StopSearchResult: stop list for user disambiguation (`stop_id`, `stop_name`, optional locality)
- FeedStatus: startup/admin status (`state`, `message`, `feed_start_date`, `feed_end_date`)
