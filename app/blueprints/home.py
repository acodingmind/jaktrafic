#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


import ssk.blueprints.home_handler
from ssk.forms.contact_form import ContactForm

from ssk.ssk_consts import SSK_ADMIN_GROUP
from ssk.globals.web_gate import WebGate

from flask import Blueprint, request
from flask import render_template

bp = Blueprint('local', __name__, url_prefix='/')


@bp.route('/', methods=['GET'])
def index():
    if WebGate.is_closed():
        return WebGate.render_closed()

    return render_template("local/start.html", admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/about', methods=['GET'])
def about():
    if WebGate.is_closed():
        return WebGate.render_closed()

    my_form = ContactForm()
    my_form.source = "about"

    return render_template("local/about.html", form=my_form, message=None, admin_group_name=SSK_ADMIN_GROUP)


@bp.route('/post_contact', methods=['POST'])
def post_contact():
    if WebGate.is_closed():
        return WebGate.render_closed()

    _, my_form, my_message = ssk.blueprints.home_handler.HomeHandler.post_contact(request)

    return render_template("local/about.html", form=my_form, message=my_message, admin_group_name=SSK_ADMIN_GROUP)
