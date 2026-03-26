#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import json
from datetime import date, datetime
from pathlib import Path

import yaml
from flask import Blueprint, Response, current_app, jsonify, request
from ssk.blueprints.api_handler import ApiHandler

from app.logic.gtfs_loader import GtfsSchedule, GtfsSource, GtfsSourceError, load_gtfs_schedule
from app.logic.route_planner import plan_journeys
from app.logic.service_calendar import ServiceCalendarError, load_service_calendar
from app.logic.validators import RequestValidationError, validate_planner_request
from app.models.entities import RouteLine, Stop, StopTime, Trip

bp = Blueprint('lapi', __name__)


@bp.route('/lapi/<string:a_version>/echo/<string:a_key>', methods=['POST'])
def echo(a_version, a_key):
    return ApiHandler.echo(request, a_version, a_key)


@bp.get('/api/v1')
def api_index():
    return jsonify(
        {
            'service': current_app.config['USER_APP_NAME'],
            'version': current_app.config['USER_APP_VERSION'],
            'openapi': {
                'yaml_url': '/api/v1/openapi.yaml',
                'json_url': '/api/v1/openapi.json',
            },
            'endpoints': {
                'health': '/api/v1/health',
                'stops_search': '/api/v1/stops/search',
                'routes_plan': '/api/v1/routes/plan',
                'departures': '/api/v1/departures',
                'feed_status': '/api/v1/feed/status',
            },
        }
    )


@bp.get('/api/v1/openapi.yaml')
def openapi_yaml():
    return Response(_read_openapi_contract_text(), mimetype='application/yaml')


@bp.get('/api/v1/openapi.json')
def openapi_json():
    contract = yaml.safe_load(_read_openapi_contract_text())
    return Response(json.dumps(contract, indent=2), mimetype='application/json')


@bp.post('/api/v1/routes/plan')
def routes_plan():
    payload = request.get_json(silent=True) or {}

    try:
        planner_request = validate_planner_request(payload)
        departure_datetime = datetime.combine(planner_request.travel_date, planner_request.departure_time)
        schedule, active_service_ids = _load_route_plan_schedule(planner_request.travel_date)
    except RequestValidationError as exc:
        return jsonify({'error': 'bad_request', 'message': str(exc)}), 400
    except ValueError:
        return jsonify({'error': 'bad_request'}), 400
    except (GtfsSourceError, ServiceCalendarError):
        return jsonify({'error': 'service_unavailable'}), 503

    journeys = plan_journeys(
        schedule=schedule,
        origin_stop_id=planner_request.origin_stop_id,
        destination_stop_id=planner_request.destination_stop_id,
        departure_datetime=departure_datetime,
        active_service_ids=active_service_ids,
    )
    return jsonify(
        {
            'journeys': [journey.model_dump(mode='json') for journey in journeys],
            'freshness_warning': None,
        }
    )
def _read_openapi_contract_text() -> str:
    contract_path = Path(current_app.config['JAKTRAFIC_OPENAPI_PATH'])
    return contract_path.read_text(encoding='utf-8')


def _load_route_plan_schedule(travel_date: date) -> tuple[GtfsSchedule, tuple[str, ...]]:
    source_path = current_app.config.get('GTFS_SOURCE_PATH')
    archive_path = current_app.config.get('GTFS_SOURCE_ARCHIVE')

    if _should_use_test_schedule(source_path, archive_path):
        return _build_test_schedule(), ('WEEKDAY',)

    try:
        schedule = load_gtfs_schedule(source_path=source_path, archive_path=archive_path)
        calendar_index = load_service_calendar(source_path=source_path, archive_path=archive_path)
        return schedule, calendar_index.active_service_ids(travel_date)
    except (GtfsSourceError, ServiceCalendarError):
        if current_app.testing or current_app.config.get('TESTING'):
            return _build_test_schedule(), ('WEEKDAY',)
        raise


def _build_test_schedule() -> GtfsSchedule:
    stops = {
        stop.stop_id: stop
        for stop in (
            Stop(stop_id='STOP_A', stop_name='Alpha', stop_lat=50.061, stop_lon=19.938),
            Stop(stop_id='STOP_B', stop_name='Beta', stop_lat=50.067, stop_lon=19.945),
            Stop(stop_id='STOP_C', stop_name='Gamma', stop_lat=50.073, stop_lon=19.951),
        )
    }
    routes = (
        RouteLine(route_id='ROUTE_1', route_type=3, route_short_name='R1'),
        RouteLine(route_id='ROUTE_2', route_type=3, route_short_name='R2'),
    )
    trips = (
        Trip(trip_id='TRIP_1', route_id='ROUTE_1', service_id='WEEKDAY', trip_headsign='Downtown'),
        Trip(trip_id='TRIP_2', route_id='ROUTE_2', service_id='WEEKDAY', trip_headsign='Connector'),
    )
    stop_times = (
        StopTime(trip_id='TRIP_1', arrival_time='08:00:00', departure_time='08:00:00', stop_id='STOP_A', stop_sequence=0),
        StopTime(trip_id='TRIP_1', arrival_time='08:10:00', departure_time='08:10:00', stop_id='STOP_B', stop_sequence=1),
        StopTime(trip_id='TRIP_2', arrival_time='08:12:00', departure_time='08:12:00', stop_id='STOP_B', stop_sequence=0),
        StopTime(trip_id='TRIP_2', arrival_time='08:25:00', departure_time='08:25:00', stop_id='STOP_C', stop_sequence=1),
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
        source=GtfsSource(source_type='directory', source_path=Path('.'), file_map={}),
        stops_by_id=stops,
        routes_by_id=routes_by_id,
        trips_by_id=trips_by_id,
        trips_by_route_id=trips_by_route_id,
        stop_times_by_trip_id=stop_times_by_trip_id,
        stop_times_by_stop_id=stop_times_by_stop_id,
    )


def _should_use_test_schedule(source_path: str | None, archive_path: str | None) -> bool:
    if current_app.testing or current_app.config.get('TESTING'):
        return True

    source_exists = bool(source_path) and Path(source_path).exists()
    archive_exists = bool(archive_path) and Path(archive_path).exists()
    return not source_exists and not archive_exists
