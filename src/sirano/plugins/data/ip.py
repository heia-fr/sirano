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


import re

from scapy.volatile import RandIP

from sirano.data import Data


class IPData(Data):
    """IP Data plugin"""

    name = 'ip'

    re_ip = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    """The regular expression for a ip address"""

    def __init__(self, app):
        super(IPData, self).__init__(app)
        self.hosts = dict()
        self.subnets = dict()

    def load(self):
        super(IPData, self).load()

        self.hosts = self.data['hosts']
        self.subnets = self.data['subnets']

    def process(self):

        for k, v in self.hosts.iteritems():
            if k is None:
                break
            if v is None:
                while True:
                    r = str(RandIP())
                    if len(r) == len(k):
                        self.hosts[k] = r
                        break

    def clear(self):
        for k in self.hosts.iterkeys():
            self.hosts[k] = ''

    def add_value(self, ip):

        if ip not in self.hosts:
            self.hosts[ip] = None

    def get_replacement(self, value):

        r = self.hosts.get(value, None)

        if r is None:
            self.app.log.error("data:ip: Replacement value not found for '%s'", value)
            return ''

        return r

    def is_valid(self, value):
        """
        Please de not use the buggy function netaddr.valid_ipv4()

        :param value: The IP address to check
        :type value: str
        """
        return self.re_ip.match(value) is not None

