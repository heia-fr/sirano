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


class Manager(object):
    """Superclass for all managers"""

    name = None
    """The name of the manager, this class attribute must be declared in subclasses"""

    def __init__(self, app):
        """
        This initializer method must be called by subclasses

        :param app: The application instance
        :type app: App
        """
        self.app = app
        """The application instance"""

        self.conf = app.conf.get(self.name, dict())
        """The manager configuration given by the YAML configuration file"""

    def configure(self):
        """Configure the manager after all the others are initialized"""
        raise NotImplementedError