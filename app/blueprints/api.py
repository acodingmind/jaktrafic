#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from flask import Blueprint, request
from ssk.blueprints.api_handler import ApiHandler

bp = Blueprint('lapi', __name__, url_prefix='/lapi')


@bp.route('/<string:a_version>/echo/<string:a_key>', methods=['POST'])
def echo(a_version, a_key):
    return ApiHandler.echo(request, a_version, a_key)
