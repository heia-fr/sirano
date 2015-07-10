# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>
import json

import logging
import os
import re
from zipfile import ZipFile
from enum import Enum
import time
from shutil import copytree
import shutil
import sys
import yaml

from sirano.action import ActionManager
from sirano.data import DataManager
from sirano.file import FileManager
from sirano.layer import LayerManager
from sirano.packet import PacketAnonymizer
from sirano.utils import makedirs, AppBase
from datadiff import diff

logging.getLogger("scapy.runtime").setLevel(logging.ERROR)

global sirano_logger
sirano_logger = None


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
        """
        The manager for Action plugins
        :type: ActionManager
        """

        self.data = DataManager(app)
        """
        The manager for Data plugins
        :type: DataManager
        """

        self.layer = LayerManager(app)
        """
        The manager for Layer plugins
        :type: LayerManager
        """

        self.file = FileManager(app)
        """
        The manager for File plugins
        :type: FileManager
        """

    def configure_all(self):
        """Configure all manager after they are instantiate"""
        self.action.configure()
        self.data.configure()
        self.layer.configure()
        self.file.configure()


class ProjectPath(AppBase):

    def __init__(self, app, project_name):
        """
        Object that contain all path for the specified project reference name
        :param project_name: The project reference name
        :type project_name: str
        """
        super(ProjectPath, self).__init__(app)

        project = 'projects/' + project_name

        self.root = project
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

        self.archives = 'projects/archives/' + project_name
        """The path for the project archive"""

    def load(self):
        """Create all dirs if not exist"""
        makedirs(self.root)
        makedirs(self.data)
        makedirs(self.input)
        makedirs(self.logs)
        makedirs(self.output)
        makedirs(self.report)
        makedirs(self.trash)
        makedirs(self.validation)
        makedirs(self.archives)

    def clean(self):
        """
        Clean the project

        It removes all project dir excepted the data directory
        """
        shutil.rmtree(self.input)
        shutil.rmtree(self.output)
        shutil.rmtree(self.report)
        shutil.rmtree(self.validation)
        shutil.rmtree(self.trash)
        shutil.rmtree(self.logs)
        shutil.copytree(self.app.default.report, self.report)  # Retrieve report base files
        self.load()


class App(object):

    def __init__(self, project_name):
        """
        The application instance

        This object contain all information and configuration about the application. An instance of this class should be
         accessible in all sirano software objects.
        :param project_name: The reference ID of the project
        """
        self.project_name = project_name
        """
        The reference name of the current project
        :type: str
        """

        self.project = ProjectPath(self, project_name)
        """
        All path for the current project
        :type: ProjectPath
        """

        self.report = None
        """
        The report data to serialialize to JSON file
        :type: dict[str, object]
        """

        self.default = ProjectPath(self, 'default')
        """
        All path for the default project
        :type: ProjectPath
        """

        self.log = None
        """
        The logging instance to logs application events
        :type: logging.Logger
        """

        self.conf = None
        """
        The YAML configuration file content
        :type: dict[str, object]
        """

        self.phase = None
        """The current phase of the application"""

        self.manager = None
        """
        Structure with all manager instances
        :type: AppManager
        """

        self.packet = None
        """
        The packet anonymizer
        :type : PacketAnonymizer
        """

    def load(self):
        """
        Load and configure the application
        """
        self.__load_log()
        self.__load_conf()
        self.project.load()
        self.__load_report()
        self.manager = AppManager(self)
        self.manager.configure_all()
        self.manager.data.load_all()
        self.packet = PacketAnonymizer(self)

    def save_report(self):
        self.report['project_name'] = self.project_name
        with open(os.path.join(self.project.report, 'report.json'), 'w+') as a_file:
            json.dump(self.report, a_file, indent=4)
        with open(os.path.join(self.project.report, 'resources/data/report.js'), 'w+') as a_file:
            a_file.write('jsondata = ' + json.dumps(self.report))

    def create(self):
        """
        Create a new project
        """
        copytree(self.default.root, self.project.root)
        self.load()
        self.log.info("Project '{}' created".format(self.project_name))

    def archive(self):
        """
        Archive the project
        """
        time_string = time.strftime("%Y-%m-%d_%H-%M-%S")
        with ZipFile(os.path.join(self.project.archives, time_string + '.zip'), 'w') as zip_file:
            for root, dirs, files in os.walk(self.project.root):
                for a_file in files:
                    filename = os.path.join(root, a_file)
                    arcname = os.path.relpath(filename, self.project.root)
                    zip_file.write(filename, arcname)

        self.project.clean()
        self.app.log.info("Project '{}' archived".format(self.project_name))

    def __load_report(self):
        """
        Load the report JSON file
        """
        report = dict()
        try:
            with open(os.path.join(self.project.report, 'report.json')) as f:
                report = json.load(f)
        except Exception as e:
            self.log.debug(e)
        self.report = report

    def __load_log(self):
        """
        Load the log handler
        """

        global sirano_logger
        log = sirano_logger

        fmt = logging.Formatter('%(asctime)s:%(levelname)8s:%(name)s:%(message)s')

        if log is not None:
            self.log = log
        else:
            log = logging.getLogger("sirano")
            sirano_logger = log

            # Console handler
            handler_console = logging.StreamHandler()
            handler_console.setLevel(logging.INFO)
            handler_console.setFormatter(fmt)
            log.addHandler(handler_console)

        if self.phase == 1:
            phase = 'discovery'
        elif self.phase == 2:
            phase = 'generation'
        elif self.phase == 3:
            phase = 'anonymisation'
        elif self.phase == 4:
            phase = 'validation'
        else:
            phase = 'others'

        # All file handler
        path = self.project.logs + '/' + phase + '/'
        makedirs(path)
        path += time.strftime("%Y-%m-%d_%H-%M-%S_")

        handler_critical = logging.FileHandler(path + 'critical.log', mode="a", encoding="utf-8")
        handler_critical.setLevel(logging.CRITICAL)
        handler_critical.setFormatter(fmt)
        handler_error = logging.FileHandler(path + 'error.log', mode="a", encoding="utf-8")
        handler_error.setLevel(logging.ERROR)
        handler_error.setFormatter(fmt)
        handler_info = logging.FileHandler(path + 'info.log', mode="a", encoding="utf-8")
        handler_info.setLevel(logging.INFO)
        handler_info.setFormatter(fmt)
        handler_debug = logging.FileHandler(path + 'debug.log', mode="a", encoding="utf-8")
        handler_debug.setLevel(logging.DEBUG)
        handler_debug.setFormatter(fmt)

        for hdlr in log.handlers:  # remove all old handlers
            if hdlr.stream == sys.stderr:
                break
            hdlr.flush()
            hdlr.close()
            log.removeHandler(hdlr)

        log.addHandler(handler_critical)
        log.addHandler(handler_error)
        log.addHandler(handler_info)
        log.addHandler(handler_debug)

        log.setLevel(logging.DEBUG)
        self.log = log

    def report_update_phase(self, name, values):
        """
        Update a phase entry in the report
        :param name: The name of the phase
        :type name: str
        :param values: The values to update
        :type values: dict
        """
        phases = self.report.setdefault('summary', dict()).setdefault('phases', list())
        """:type: list[dict]"""
        phase = None
        for p in phases:
            if p['name'] == name:
                phase = p
        if phase is None:
            phase = {'name': name}
            phases.append(phase)
        phase.update(values)

    def __load_conf(self):
        """
        Load the YAML configuration
        """
        self.log.debug("app: Load config: Filetype \"%s\"", self.project.config)
        current = yaml.load(open(self.project.config))
        default = yaml.load(open(self.default.config))
        self.__create_conf_diff(current, default)
        self.conf = current

    def __create_conf_diff(self, current, default):
        """
        Create the configuration diff
        :param current: The current project conf
        :param default: The default project conf
        """
        diff_string = str(diff(default, current, fromfile='default', tofile='current'))
        # :type: str

        # Fix for patch format
        regex = re.compile(r"^(\s+)(\-|\+|(?:@@.*@@))(.*)$")
        lines = diff_string.splitlines()

        for index, line in enumerate(lines):
            match = regex.match(line)
            if match:
                lines[index] = match.group(2) + match.group(1) + match.group(3)

        with open(os.path.join(self.project.data, 'config-diff.patch'), 'w+') as a_file:
            a_file.write('\n'.join(lines))


