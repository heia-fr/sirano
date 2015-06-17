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

from curses.ascii import isdigit
from random import randint
import re

from sirano.data import Data


class PhoneData(Data):
    """Phone number Data plugin"""

    name = 'phone'

    re_number = re.compile(r"^\+?\d*$")
    """The regular expression for a phone number"""

    def __init__(self, app):
        super(PhoneData, self).__init__(app)

        self.prefix = dict()
        self.codes = dict()
        self.numbers = dict()

    def get_replacement(self, value):

        r = self.numbers.get(value, None)

        if r is None:
            self.app.log.error("data:phone: Replacement value not found for '%s'", value)
            return ''

        return r

    def post_load(self):
        self.numbers = self.link_data('numbers', dict)
        self.prefix = self.link_data('prefix', dict)
        self.codes = self.link_data('codes', dict)

    def clear(self):
        for k in self.numbers.iterkeys():
            self.numbers[k] = ''

    def process(self):
        for k, v in self.numbers.iteritems():
            if v is None:
                r = ''
                for c in k:
                    if isdigit(c):
                        c = randint(0, 9)
                    r += str(c)
                self.numbers[k] = r

    def is_valid(self, value):

        if not isinstance(value, str):
            return False

        return self.re_number.match(value) is not None

    def add_value(self, value):

        if value not in self.numbers:
            self.numbers[value] = None