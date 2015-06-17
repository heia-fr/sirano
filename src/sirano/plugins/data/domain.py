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
import re
import string

from sirano.data import Data


class DomainData(Data):
    """
    Domain Data plugin
    """

    name = 'domain'

    re_domain = re.compile(r"^([a-z0-9]+(-[a-z0-9]+)*\.)+[a-z0-9]{2,}$")
    """The regular expression for a domain name"""

    def __init__(self, app):
        super(DomainData, self).__init__(app)
        self.domains = dict()

    def get_replacement(self, value):

        r = self.domains.get(value, None)

        if r is None:
            self.app.log.error("data:domain: Replacement value not found for '%s'", value)
            return ''

        return r

    def load(self):
        super(DomainData, self).load()

        self.domains = self.data['domains']

    def process(self):

        for k, v in self.domains.iteritems():
            if v is None:
                r = ''
                for c in k:
                    if c is not '.':
                        c = random.choice(string.ascii_lowercase)
                    r += c

                self.domains[k] = r

    def clear(self):
        for k in self.domains.iterkeys():
            self.domains[k] = ''

    def is_valid(self, value):

        if not isinstance(value, str):
            return False

        # Check if it is not an IP address to avoid confusion
        if self.app.manager.data.get_data('ip').is_valid(value):
            return False

        return self.re_domain.match(value) is not None

    def add_value(self, value):

        if value not in self.domains:
            self.domains[value] = None


