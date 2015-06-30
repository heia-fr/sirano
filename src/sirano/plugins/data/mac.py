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

import netaddr

from sirano.data import Data


class MacData(Data):
    """Mac Data plugin"""

    name = 'mac'

    re_mac_find = re.compile(r"((?:[0-9a-fA-F]{2}[:\.-]?){5}[0-9a-fA-F]{2})", re.IGNORECASE)
    """Simple regegular expression to find MAC addresses"""

    re_mac = re.compile(r"^((?:(?:(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2})|(?:(?:[0-9A-F]{4}\.){2}[0-9A-F]{4})))$", re.IGNORECASE)
    """
    The regular expression for a MAC addresses

    Supported format:
    -----------------
    01-23-45-67-89-ab
    01:23:45:67:89:ab
    0123.4567.89ab
    """

    def __init__(self, app):
        super(MacData, self).__init__(app)
        self.macs = None
        """
        The MAC addresses with replacement values
        :type : dict
        """

        self.exclusion = set()
        """
        The MAC addresses to not anonymize
        :type: set[str]
        """

    def post_load(self):
        self.__post_load_macs()
        self.__post_load_exclusion()

    def pre_save(self):
        for value, replacement in self.macs.items():
            self.data_report_value('mac' ,value, replacement)

    @staticmethod
    def __oui(eui):
        oui = eui.value >> 24

        return "%02X-%02X-%02X" % ((oui >> 16) & 0xff,
                                   (oui >> 8) & 0xff,
                                   oui & 0xff)

    def process(self):
        for k, v in self.macs.items():
            self.data_report_processed('mac', 'number')
            if v is None:
                if k in self.exclusion:
                    self.macs[k] = k
                else:
                    try:
                        self.macs[k] = None
                        n = netaddr.EUI(k)
                        oui = self.__oui(n)
                        r = "{}-{:02X}-{:02X}-{:02X}".format(oui,
                                                             random.randint(0x00, 0x7f),
                                                             random.randint(0x00, 0xff),
                                                             random.randint(0x00, 0xff))
                        self.macs[k] = r.replace('-', ':').lower()
                    except Exception as e:
                        self.data_report_processed('mac', 'error')
                        self.app.log.error("sirano:data:mac: Fail to generate a replacement value, mac='{}',"
                                           "exception='{}', message='{}'".format(k, type(e), e.message))
                        raise
                self.data_report_processed('mac', 'processed')

    def _add_value(self, value):
        if value not in self.macs:
            self.macs[value] = None
            return True
        return False

    def _get_replacement(self, value):
        r = self.macs.get(value, None)
        if r is None:
            self.app.log.error("data:mac: Replacement value not found for '%s'", value)
            return ''
        return r

    def is_valid(self, value):

        if not isinstance(value, str):
            return False

        valid =  self.re_mac.match(value) is not None
        return valid

    def get_number_of_values(self):
        return len(self.macs)

    def has_replacement(self, replacement):
        return replacement in self.macs.values()

    def has_value(self, value):
        return self.macs.has_key(value)

    def __getattribute__(self, name):
        return super(MacData, self).__getattribute__(name)

    def _find_values(self, string):
        founds = self.re_mac_find.findall(string)
        values = filter(lambda v: self.is_valid(v), founds)
        return values

    def __post_load_macs(self):
        """
        Called by post_load() to load internal representation of macs
        """
        self.macs = self.link_data('macs', dict)
        for k, v in self.macs.items():
            old_k = k
            k = k.lower()
            if netaddr.valid_mac(k) is False:
                self.app.log.error("data:mac: Invalid key format '{}: File {}".format(k, self.path))
                continue
            if v is not None:
                v = v.lower()
                if netaddr.valid_mac(k) is False:
                    self.app.log.error("data:mac: Invalid value format '{}: File {}".format(k, self.path))
                    continue
            del self.macs[old_k]
            self.macs[k] = v

    def __post_load_exclusion(self):
        """
        Called by post_load() to load internal representation of exception
        """
        exclusion = self.conf.get('exclusion')
        if isinstance(exclusion, list):
            for mac in exclusion:
                self.exclusion.add(mac)

    class MacAddress(object):

        #: Regex for the standard IEEE 802 format for printing MAC-48 addresses (case insensitive)
        re_mac_address = re.compile(r"^([0-9A-F]{2}[:-]){5}([0-9A-F]{2})$", re.IGNORECASE)

        def __init__(self, string):
            """
            Create a new MacAddress from the specified string.
            :param string: The string
            :type string: str
            :raise ValueError: if the string format is incorrect
            """
            if not self.is_valid(string):
                raise ValueError('Invalid MacAddress string: "{}"'.format(string))

        @classmethod
        def is_valid(cls, string):
            """
            Test if the specified string is a valid MAC address
            :param string: The string
            :return: True if valid, False if invalid
            """
            return cls.re_mac_address.match(string) is not None








