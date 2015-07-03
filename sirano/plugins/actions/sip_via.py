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

from sirano.action import Action
from sirano.exception import UnsupportedFormatException


class SIPViaAction(Action):
    """Action plugin for the field via of the protocol SIP"""

    name = 'sip-via'

    re_via = re.compile(r"^SIP/\d.\d/(UDP|TCP)\s(?P<host>[^:;]+)(:(?P<port>\d+))?\s*?((;|\?)(?P<params>.*))?$")
    """
    Regex for SIP Via

    Tested with examples in the RFC3261:

        SIP/2.0/UDP erlang.bell-telephone.com:5060;branch=z9hG4bK87asdks7
        SIP/2.0/UDP 192.0.2.1:5060 ;received=192.0.2.207;branch=z9hG4bK77asjd

    """

    def discover(self, value):
        via = self.re_via.match(value)

        if via is None:
            raise UnsupportedFormatException("action = '{}', value = ".format(self.name, repr(value)))

        host = via.group('host')
        # params = via.group('params')

        self.app.manager.data.add_value(host)

        # TODO check params

    def anonymize(self, value):
        via = self.re_via.match(value)

        if via is None:
            raise UnsupportedFormatException("action = '{}', value = ".format(self.name, repr(value)))

        host = via.group('host')

        value = value.replace(host, self.app.manager.data.get_replacement(host))

        # TODO replace params

        return value
