#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

import inspect
import os
import shutil

from flask import Flask

import ssk
from ssk import init_ssk, start_ssk
from pathlib import Path


def create_app(testing=None):
    my_app_templates = "app/templates"
    my_app_static = "app/static"

    my_ssk_path = os.path.dirname(inspect.getfile(ssk))
    my_ssk_templates = "{}/templates/".format(my_ssk_path)
    my_ssk_static = "{}/static/".format(my_ssk_path)

    if Path(my_app_templates).is_symlink():
        os.unlink(my_app_templates)
    os.symlink(my_ssk_templates, my_app_templates)

    if Path(my_app_static).is_symlink():
        os.unlink(my_app_static)
    os.symlink(my_ssk_static, my_app_static)

    shutil.rmtree("app/templates/local", ignore_errors=True)
    shutil.copytree("app/html/local", "app/templates/local")

    shutil.rmtree("app/static/local", ignore_errors=True)
    shutil.copytree("app/assets/local", "app/static/local")

    my_instance_path = os.path.join(os.getcwd(), 'ins')
    my_app = Flask(__name__, instance_relative_config=True, instance_path=my_instance_path)

    from .logic.app_logic import AppLogic
    from .db_upgrader import DbUpgrader

    my_app = init_ssk(my_app, AppLogic, DbUpgrader, testing)
    start_ssk(my_app, testing)
    my_app.logger.info("create_app {} v. {} soseki ver {} end".format(my_app.config["USER_APP_NAME"],
                                                                       my_app.config["USER_APP_VERSION"],
                                                                       my_app.config["SSK_VER"]))

    from app.blueprints import home
    my_app.register_blueprint(home.bp)

    from app.blueprints import api
    my_app.register_blueprint(api.bp)

    return my_app
