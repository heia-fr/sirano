#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
#
# Sirano is a network trace and log file anonymizer.
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

"""SIRANO - SIP/RTP Trafic Anonymizer"""

import argparse
import os
import unittest

from sirano.app import App, Phase


class Sirano:
    """
    Class for the sirano launcher
    """
    def __init__(self):
        pass

    @staticmethod
    def phase_1(project_name):
        """
        Discovery phase
        """
        app = App(project_name)
        app.load()

        app.phase = Phase.phase_1
        app.manager.file.add_files()
        app.manager.file.discover_all()
        app.manager.data.save_all()
        app.log.info("Phase 1: discovery complete")
        app.save_report()

    @staticmethod
    def phase_2(project_name):
        """
        Generation phase
        """
        app = App(project_name)
        app.load()

        app.phase = Phase.phase_2
        app.manager.data.process_all()
        app.manager.data.save_all()
        app.log.info("Phase 2: generation complete")
        app.save_report()

    @staticmethod
    def phase_3(project_name):
        """
        Anonymization phase
        """
        app = App(project_name)
        app.load()

        app.phase = Phase.phase_3
        app.manager.file.add_files()
        app.manager.file.anonymize_all()
        app.log.info("Phase 3: anonymization complete")
        app.save_report()

    @staticmethod
    def phase_4(project_name):
        """
        Validation phase
        """
        app = App(project_name)
        app.load()

        app.phase = Phase.phase_4
        app.manager.file.add_files()
        app.manager.file.validate_all()
        app.log.info("Phase 4: validation complete")
        app.save_report()

    @staticmethod
    def pass_through(project_name):
        """
        Pass through all phases
        """
        app = App(project_name)
        app.load()

        app.log.info("Pass throught start")
        app.phase = Phase.phase_1
        app.manager.file.add_files()
        app.manager.file.discover_all()
        app.manager.data.save_all()
        app.log.info("Phase 1: discovery complete")

        app.phase = Phase.phase_2
        app.manager.data.process_all()
        app.manager.data.save_all()
        app.log.info("Phase 2: generation complete")

        app.phase = Phase.phase_3
        app.manager.file.anonymize_all()
        app.log.info("Phase 3: anonymization complete")

        app.phase = Phase.phase_4
        app.manager.file.validate_all()
        app.log.info("Phase 4: validation complete")

        app.save_report()

    @staticmethod
    def create(project_name):
        """
        Create a new project
        :param project_name: The project name
        :type project_name: str
        """
        app = App(project_name)
        app.create()

    @staticmethod
    def archive(project_name):
        """
        Archive the project
        :param project_name: The project name
        :type project_name: str
        """
        app = App(project_name)
        app.archive()


if __name__ == '__main__':
    __author__ = "Loic Gremaud <loic.gremaud@grelinfo.ch>"
    __copyright__ = "Copyright (C) 2015 Loic Gremaud"
    __license__ = "Licence"
    __version__ = "0.2.1"

    parser = argparse.ArgumentParser("sirano")
    subparsers = parser.add_subparsers(title='action', help="The action to start", dest="action")

    parser_process = subparsers.add_parser('process', help="Process a anonymization phase")
    parser_process.add_argument("phase", type=int, choices=[0, 1, 2, 3, 4],
                                help="The phase number : {"
                                     "0: pass through, "
                                     "1: discovery, "
                                     "2: generation, "
                                     "3: anonymization and "
                                     "4: validation}")
    parser_process.add_argument("project", help="The project name")

    parser_create = subparsers.add_parser('create', help="Create a new project")
    parser_create.add_argument("project", help="The project name")

    parser_archive = subparsers.add_parser('archive', help="Archive an existent project")
    parser_archive.add_argument("project", help="The project name")

    args = parser.parse_args()

    if args.action == "process":
        if not os.path.isdir("projects/" + args.project):
            parser.error("Project '{}' not exists".format(args.project))
            exit(1)
        if args.phase == 0:
            Sirano.pass_through(args.project)
        elif args.phase == 1:
            Sirano.phase_1(args.project)
        elif args.phase == 2:
            Sirano.phase_2(args.project)
        elif args.phase == 3:
            Sirano.phase_3(args.project)
        elif args.phase == 4:
            Sirano.phase_4(args.project)
    elif args.action == "create":
        Sirano.create(args.project)
    elif args.action == "archive":
        if not os.path.isdir("projects/" + args.project):
            parser.error("Project '{}' not exists".format(args.project))
            exit(1)
        Sirano.archive(args.project)
