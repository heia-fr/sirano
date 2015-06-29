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
import struct
from dns import rdata, message
from scapy.layers.dns import DNSRR, DNSgetstr, DNSRRField
from scapy.packet import ls

from sirano.action import Action
from sirano.exception import UnsupportedFormatException, ImplicitDropException


class DNSRDataAction(Action):
    """Action plugin for DNS ressource data"""

    name = 'dns-rdata'

    re_ptr = re.compile(r"^((?:\d{1,3}\.){3}\d{1,3})\.in-addr\.arpa\.?$")

    def __init__(self, app):
        super(DNSRDataAction, self).__init__(app)

        self.domain_name = self.app.manager.action.get_action('domain-name')
        """
        Action domaine-name plugin
        :type: Action
        """


    def discover(self, value):

        packet = self.app.packet.current_packet

        if not DNSRR in packet:
            raise ImplicitDropException("No DNSRR layer found")

        dnsrr = packet[DNSRR]
        a_type = dnsrr.type

        if a_type == 1: # A
            self.app.manager.data.get_data('ip').add_value(value)
            return
        elif a_type in [5, 12]: # A, CNAME, PTR
            self.domain_name.discover(value)
            return


        raise ImplicitDropException("Type not supported, type = '{}'".format(a_type))

    def anonymize(self, value):
        packet = self.app.packet.current_packet

        if not DNSRR in packet:
            raise ImplicitDropException("No DNSRR layer found")

        dnsrr = packet[DNSRR]
        a_type = dnsrr.type

        if a_type == 1: # A
            return self.app.manager.data.get_data('ip').get_replacement(value)
        elif a_type in [5, 12]: # A, CNAME, PTR
            return self.domain_name.anonymize(value)

        raise ImplicitDropException("Type not supported, type = '{}'".format(a_type))

