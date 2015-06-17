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
from sirano.plugins.data.domain import DomainData
from sirano.plugins.data.ip import IPData
from sirano.plugins.data.mac import MacData


class AutoAction(Action):
    """
    Action plugin for unknown data structures (automatic)
    """

    name = "auto"

    re_ip = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")
    """Simplified regular expression for finding IPv4 Addresses"""

    re_domain = re.compile(r"(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,6}")
    """
    The regular expression for a domain name

    Domain can be in URI or e-mail so there no word boundary '\b'
    """

    re_mac = re.compile(r"\b(?:(?:(?:[0-9A-F]{2}[:-]){5}[0-9A-F]{2})|(?:(?:[0-9A-F]{4}\.){2}[0-9A-F]{4}))\b",
                        re.IGNORECASE)
    """
    The regular expression for a mac adress

    Supported format:
    -----------------
    01-23-45-67-89-ab
    01:23:45:67:89:ab
    0123.4567.89ab
    """

    re_email = re.compile(r"\b([a-zA-Z0-9._%+-]+)(?:@(?:[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}))\b")
    """The regular expression for name and domain name in e-mail"""

    # re_phone = re.compile(r"(?:^|\s|)(\+?(?:\d[\s\.-]?){2,}\d)(?:\s|$)")
    re_phone = re.compile(r"(?:\+|0{2,})(?:\d\s?){6,14}\d")
    """The regular expression for finding phone numbers (E.164 format)"""

    re_word = re.compile(r"([\s'\"@]+)")
    """The regular expression used to split line into word for finding the names"""

    def __init__(self, app):
        super(AutoAction, self).__init__(app)

    def __discover_generic(self, value, regex, data):
        """
        Generic method for the discover process
        :param value: the value to parse
        :type value: str
        :param regex: the regular expression to find
        :type regex: re
        :param data: the name of the data manager to use
        :type data: str
        """
        # :type Data
        data = self.app.manager.data.get_data(data)
        # :type list[str]
        list = regex.findall(value)
        # Remove duplicates
        list = set(list)
        for e in list:
            if data.is_valid(e):
                data.add_value(e)

    def __anonymize_generic(self, value, regex, data):
        """
        Generic method for the anonymize process
        :param value: the value to parse
        :type value: str
        :param regex: the regular expression to find
        :type regex: re
        :param data: the name of the data manager to use
        :type data: str
        :return The anonymized value
        :rtype str
        """
        # :type Data
        data = self.app.manager.data.get_data(data)
        # :type list[str]
        list = regex.findall(value)

        for e in list:
            if data.is_valid(e):
                new_e = data.get_replacement(e)
                value = value.replace(e, new_e)

        return value

    def __anonymize_name(self, value):
        # :type NameData
        data = self.app.manager.data.get_data('name')
        words = self.re_word.split(value)
        for idx, word in enumerate(words):
            if data.has_replacement(word):
                words[idx] = data.get_replacement(word)
        value = ''.join(words)
        return value

    def discover(self, value):
        self.__discover_generic(value, self.re_ip, 'ip')
        self.__discover_generic(value, self.re_domain, 'domain')
        self.__discover_generic(value, self.re_mac, 'mac')
        self.__discover_generic(value, self.re_email, 'name')
        self.__discover_generic(value, self.re_phone, 'phone')

    def anonymize(self, value):
        value = self.__anonymize_generic(value, self.re_ip, 'ip')
        value = self.__anonymize_generic(value, self.re_domain, 'domain')
        value = self.__anonymize_generic(value, self.re_mac, 'mac')
        value = self.__anonymize_generic(value, self.re_phone, 'phone')
        value = self.__anonymize_name(value)
        return value

