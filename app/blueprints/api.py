#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import json
from pathlib import Path

import yaml
from flask import Blueprint, Response, current_app, jsonify, request
from ssk.blueprints.api_handler import ApiHandler

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


def _read_openapi_contract_text() -> str:
    contract_path = Path(current_app.config['JAKTRAFIC_OPENAPI_PATH'])
    return contract_path.read_text(encoding='utf-8')
