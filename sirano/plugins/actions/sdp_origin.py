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


class SDPOriginAction(Action):
    """Action plugin for the field C of the protocol SDP"""

    name = "sdp-origin"

    re_sdp_origin = re.compile(r"^(?P<username>.+)\s"
                               r"(?P<session_id>.+)\s"
                               r"(?P<version>.+)\s"
                               r"(?P<network_type>IN)\s"
                               r"(?P<address_type>IP4)\s"
                               r"(?P<address>.+)$")
    """
    The regular expression for the field O

    RFC2327 :
    ---------
    o=<username> <session id> <version> <network type> <address type> <address>

    network type : IN
    address type : IP4
    """

    def __init__(self, app):
        super(SDPOriginAction, self).__init__(app)

        self.data_ip = self.app.manager.data.get_data('ip')
        self.data_name = self.app.manager.data.get_data('name')

    def __parse(self, value):
        """
        Parse the value
        :param value: The value to parse
        :type value: str
        :return: The ip and the name
        :rtype (str, str)
        """

        m = self.re_sdp_origin.match(value)

        if m is None:
            raise UnsupportedFormatException()

        ip = m.group('address')
        name = m.group('username')

        if self.data_name.is_valid(name) and self.data_ip.is_valid(ip):
            return ip, name
        else:
            raise UnsupportedFormatException()

    def discover(self, value):

        ip, name = self.__parse(value)

        self.data_name.add_value(name)
        self.data_ip.add_value(ip)

    def anonymize(self, value):

        ip, name = self.__parse(value)

        value = value.replace(name, self.data_name.get_replacement(name))
        value = value.replace(ip, self.data_ip.get_replacement(ip))

        return value
