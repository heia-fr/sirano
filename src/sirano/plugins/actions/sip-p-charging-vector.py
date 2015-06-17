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


class SIPPChargingVectorAction(Action):
    """Action plugin for the field Charging-Vector of the protocol SIP"""

    name = "sip-p-charging-vector"

    re_p_charging_vector = re.compile(r"^icid-value=[^;]*;icid-generated-at=(?P<ip_address>.*)$")
    """The regular expression for the format of the Charging-Vector field"""

    def __init__(self, app):
        super(SIPPChargingVectorAction, self).__init__(app)

        ip = self.app.manager.data.get_data('ip')

        self.ip = ip

    def discover(self, value):

        # l = value.split(';')

        p_charging_vector = self.re_p_charging_vector.match(value)

        if p_charging_vector is None:
            self.app.log.error("action:sip-p-charging-vector: Unknown format for '{}'".format(value))
            return

        ip = p_charging_vector.group('ip_address')

        self.ip.add_value(ip)

    def anonymize(self, value):

        p_charging_vector = self.re_p_charging_vector.match(value)

        if p_charging_vector is None:
            self.app.log.error("action:sip-p-charging-vector: Unknown format for '{}'".format(value))
            return ''

        ip = p_charging_vector.group('ip_address')

        return value.replace(ip, self.ip.get_replacement(ip))

