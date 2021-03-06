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
import struct
import netaddr
from scapy.fields import MACField
from scapy.utils import str2mac, mac2str

from sirano.action import Action


class MacAddressAction(Action):
    """Action plugin for a mac address"""

    name = "mac-address"

    def __init__(self, app):
        super(MacAddressAction, self).__init__(app)

        self.mac = self.app.manager.data.get_data('mac')
        """:type : MacData"""

    def discover(self, value):
        if '\x00' in value:
            value = str(str2mac(value[0:6]))

        self.mac.add_value(value)

    def anonymize(self, value):
        binary = False
        if '\x00' in value:
            value = str(str2mac(value[0:6]))
            binary = True
        replacement = self.mac.get_replacement(value)
        if binary:
            if replacement != '':
                replacement = mac2str(replacement)
        return replacement
