# -*- coding: utf-8 -*-
#
# This file is a part of Sirano.
#
# Copyright (C) 2015  HES-SO // HEIA-FR
# Copyright (C) 2015  Loic Gremaud <loic.gremaud@grelinfo.ch>
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

import logging
import os
from enum import Enum
import errno
import yaml

from sirano.action import ActionManager
from sirano.data import DataManager
from sirano.file import FileManager
from sirano.layer import LayerManager
from sirano.packet import PacketAnonymizer
from sirano.utils import makedirs, AppBase


class Phase(Enum):
    phase_1 = 1
    phase_2 = 2
    phase_3 = 3
    phase_4 = 4
    """Validation phase"""

class AppManager(AppBase):
    def __init__(self, app):
        """
        Object that contain all manager instance
        """
        super(AppManager, self).__init__(app)

        self.action = ActionManager(app)
        """The manager for Action plugins"""

        self.data = DataManager(app)
        """The manager for Data plugins"""

        self.layer = LayerManager(app)
        """The manager for Layer plugins"""

        self.file = FileManager(app)
        """The manager for File plugins"""

    def configure_all(self):
        """Configure all manager after they are instantiate"""
        self.action.configure()
        self.data.configure()
        self.layer.configure()
        self.file.configure()


class ProjectPath(object):

    def __init__(self, project_id):
        """
        Object that contain all path for the specified project reference id

        :param project_id: The reference id of the project
        """

        project = 'projects/' + project_id

        self.project = project
        """The path of the project folder"""

        self.data = project + '/data'
        """The path of the folder that contain config and data YAML files"""

        self.output = project + '/out'
        """The path of the output folder than will contain all anonymized files"""

        self.input = project + '/in'
        """The path of the input folder that contain all files to anonymize"""

        self.trash = project + '/trash'
        """The path of the trash folder that contain all deleted data"""

        self.report = project + '/report'
        """The path of the report folder that contain logs and result reports"""

        self.config = self.data + '/config.yml'
        """The path of the config file"""

        self.validation = project + '/validation'
        """The path of the validation file"""

        self.logs = project + '/logs'
        """The path for the log files"""

        self.__create_dirs()


    def __create_dirs(self):
        """Create all dirs if not exist"""
        makedirs(self.project)
        makedirs(self.data)
        makedirs(self.input)
        makedirs(self.logs)
        makedirs(self.output)
        makedirs(self.report)
        makedirs(self.trash)
        makedirs(self.validation)

class App(object):
    def __init__(self, project_id):
        """
        The application instance

        This object contain all information and configuration about the application. An instance of this class should be
         accessible in all sirano software objects.
        :param project_id: The reference ID of the project
        """

        self.project_id = project_id
        """The reference ID of the current project"""

        self.project = ProjectPath(project_id)
        """All path for the current project"""

        self.default = ProjectPath('default')
        """All path for the default project"""

        self.log = self.__get_log()
        """ The logging instance to logs application events"""

        self.conf = self.__get_yml()
        """The XAML configuration file content"""

        self.phase = None
        """The current phase of the application"""

        self.manager = AppManager(self)
        """All manager instances"""

        self.manager.configure_all()

        self.packet = PacketAnonymizer(self)
        """
        The packet anonymizer
        :type : PacketAnonymizer
        """

    def __get_log(self):

        log = logging.getLogger("sirano")
        log.setLevel(logging.DEBUG)

        fmt = logging.Formatter('%(levelname)8s:%(name)s:%(message)s')

        # Console handler
        handler_console = logging.StreamHandler()
        handler_console.setLevel(logging.WARNING)
        handler_console.setFormatter(fmt)

        # All file handler
        path = self.project.logs + '/'

        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

        handler_critical = logging.FileHandler(path + 'critical.log', mode="w", encoding="utf-8")
        handler_critical.setLevel(logging.CRITICAL)
        handler_error = logging.FileHandler(path + 'error.log', mode="w", encoding="utf-8")
        handler_error.setLevel(logging.ERROR)
        handler_info = logging.FileHandler(path + 'info.log', mode="w", encoding="utf-8")
        handler_info.setLevel(logging.INFO)
        handler_debug = logging.FileHandler(path + 'debug.log', mode="w", encoding="utf-8")
        handler_debug.setLevel(logging.DEBUG)

        log.addHandler(handler_console)
        log.addHandler(handler_critical)
        log.addHandler(handler_error)
        log.addHandler(handler_info)
        log.addHandler(handler_debug)

        log.info("app: Sirano logs in console")

        return log

    def __get_yml(self):
        self.log.info("app: Load config: Filetype \"%s\"", self.project.config)

        f = file(self.project.config)  # Read only by default
        yml = yaml.load(f)

        return yml