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

import random
import string

from sirano.data import Data


class NameData(Data):
    """Name Data plugin"""

    name = 'name'

    def __init__(self, app):
        super(NameData, self).__init__(app)

        self.names = dict()

    def add_value(self, value):
        assert isinstance(value, str)

        if value not in self.names:
            self.names[value] = None

    def process(self):

        for k, v in self.names.iteritems():
            if v is None:

                r = ''
                for _ in k:
                    r += random.choice(string.letters)
                self.names[k] = r

    def clear(self):
        for k in self.names.iterkeys():
            self.names[k] = ''

    def load(self):
        super(NameData, self).load()

        self.names = self.data['names']

    def get_replacement(self, value):

        r = self.names.get(value, None)

        if r is None:
            self.app.log.error("data:name: Replacement value not found for '%s'", value)
            return ''

        return r

    def is_valid(self, value):
        d = self.app.manager.data

        # Check if it is not an phone numbers, ip address or domain name to avoid confusion
        if d.get_data('phone').is_valid(value) or d.get_data('domain').is_valid(value) or d.get_data('ip').is_valid(
                value):
            return False

        return True