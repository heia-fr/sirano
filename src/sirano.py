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

from sirano.app import App, Phase


class Sirano:
    """
    Class for the sirano launcher
    """

    def __init__(self, project_id):
        """
        Initialize the Sirano launcher

        :param project_id: The project reference id
        :type project_id: str
        """
        self.app = App(project_id)
        self.app.manager.data.load_all()

    def phase_1(self):
        """
        Discovery phase
        """

        self.app.phase = Phase.phase_1
        self.app.manager.file.add_files()
        self.app.manager.file.discover_all()
        self.app.manager.data.save_all()
        self.app.log.info("Phase 1: discovery complete")

    def phase_2(self):
        """
        Generation phase
        """

        self.app.phase = Phase.phase_2
        self.app.manager.data.process_all()
        self.app.manager.data.save_all()
        self.app.log.info("Phase 2: generation complete")

    def phase_3(self):
        """
        Anonymization phase
        """
        self.app.phase = Phase.phase_3
        self.app.manager.file.add_files()
        self.app.manager.file.anonymize_all()
        self.app.log.info("Phase 3: anonymization complete")

    def phase_4(self):
        """
        Validation phase
        """
        self.app.phase = Phase.phase_4
        self.app.manager.file.add_files()
        self.app.manager.data.clear_all()
        self.app.manager.file.validate_all()
        self.app.log.info("Phase 4: validation complete")

    def pass_through(self):
        """
        Pass through all phases
        """
        self.app.phase = Phase.phase_1
        self.app.manager.file.add_files()
        self.app.manager.file.discover_all()
        self.app.log.info("Phase 1: discovery complete")

        self.app.phase = Phase.phase_2
        self.app.manager.data.process_all()
        self.app.manager.data.save_all()
        self.app.log.info("Phase 2: generation complete")

        self.app.phase = Phase.phase_3
        self.app.manager.file.anonymize_all()
        self.app.log.info("Phase 3: anonymization complete")

        self.app.phase = Phase.phase_4
        self.app.manager.data.clear_all()
        self.app.manager.file.validate_all()
        self.app.log.info("Phase 4: validation complete")

if __name__ == '__main__':
    __author__ = "Loic Gremaud <loic.gremaud@grelinfo.ch>"
    __copyright__ = "Copyright (C) 2015 Loic Gremaud"
    __license__ = "Licence"
    __version__ = "0.1.2"

    parser = argparse.ArgumentParser("sirano")
    parser.add_argument("project", help="The project reference ID")
    parser.add_argument("phase", type=int, choices=[0, 1, 2, 3, 4],
                        help="The phase number ("
                             "0 = pass through, "
                             "1 = discovery, "
                             "2 = generation, "
                             "3 = anonymization and "
                             "4 = validation)")

    args = parser.parse_args()

    sirano = Sirano(args.project)

    if args.phase == 0:

        sirano.pass_through()

    elif args.phase == 1:

        sirano.phase_1()

    elif args.phase == 2:

        sirano.phase_2()

    elif args.phase == 3:

        sirano.phase_3()

    elif args.phase == 4:

        sirano.phase_4()

