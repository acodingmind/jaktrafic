#
# Copyright (c) 2023 Michał Świtała / CodingMinds.io
# SPDX-License-Identifier: MIT
#

from ssk.logic.cmd.root_cmd import RootCmd
from ssk.globals.job_mgr import JobMgr


class AppLogic:
    _job_mgr = None

    @staticmethod
    def get_instance():
        return AppLogic()

    def get_id(self):
        # this is a default logic
        return 0

    def __init__(self):
        self._job_mgr = JobMgr()

    def get_job_mgr(self):
        return self._job_mgr

    def get_root_cmd(self):
        return RootCmd()


