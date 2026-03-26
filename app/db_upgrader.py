#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#


from flask import current_app
from ssk.db import get_version, set_version


class DbUpgrader:
    @staticmethod
    def ver1():
        my_version = 1
        current_app.logger.info("upgrading to {}".format(my_version))

        my_db_version = get_version()

        if my_db_version.db_version < my_version:
            set_version(my_version)

    @staticmethod
    def get_upgrade_functions():
        my_retval = [DbUpgrader.ver1]

        return my_retval
