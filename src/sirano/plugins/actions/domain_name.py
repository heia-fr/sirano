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
from sirano.exception import UnsupportedFormatException, ImplicitDropException


class DomainNameAction(Action):
    """Action plugin for a domain name"""

    name = "domain-name"

    re_e164 = re.compile(r"^(?P<number>(?:\d\.){1,15})e164\.arpa(?:\.)?$", re.IGNORECASE)
    """
    Regular expression to extract E.164 number with dot and reversed
    """

    re_ptr = re.compile(
        r"^(?:(?:(?P<ip_reversed>(?:\d{1,3}\.){3}\d{1,3})\.in-addr\.arpa\.?)|(?P<ip>(?:\d{1,3}\.){3}\d{1,3}))$",
        re.IGNORECASE)
    """
    Regular expression to extract IPv4 address with byte reversed
    """

    def __init__(self, app):
        super(DomainNameAction, self).__init__(app)

        domain = self.app.manager.data.get_data('domain')

        self.domain = domain
        """
        The domain name data manager
        :type: sirano.plugins.data.domain.DomainData
        """

        self.phone = self.app.manager.data.get_data('phone')
        """
        The phone number data manager
        :type: sirano.plugins.data.phone.PhoneData
        """

        self.ip = self.app.manager.data.get_data('ip')
        """
        The ip adress data manager
        :type: sirano.plugins.data.ip.IPData
        """

    def discover(self, value):
        if value == ".":
            return

        if not self.__discover_ip_address(value):
            if not self.__discover_phone(value):
                if not self.__discover_domain(value):
                    if not self.__discover_name(value):
                        self.app.log.error("sirano:data:domain-name: Invalid format, value = '{}'".format(value))
                        raise ImplicitDropException()

    def anonymize(self, value):
        if value == ".":
            return value

        replacement = self.__anonymize_ip_address(value)
        if replacement is None:
            replacement = self.__anonymize_phone(value)
            if replacement is None:
                replacement = self.__anonymize_domain(value)
                if replacement is None:
                    replacement = self.__anonymize_name(value)
                    if replacement is None:
                        self.app.log.error("sirano:data:domain-name: Invalid format, value = '{}'".format(value))
                        raise ImplicitDropException()
        return replacement

    def __value_to_ip_address(self, value):
        """
        Transform a DNS entry to an ip address
        :param value: The DNS entry
        :type value: str
        :return: The ip address or None
        :rtype: str: None
        """
        match = self.re_ptr.match(value)

        if match is None:
            return None

        ip = match.group('ip')
        ip_reversed = match.group('ip_reversed')

        if ip_reversed:
            # Reverse byte to the correct order
            ip_reversed = ip_reversed.split('.')
            ip_reversed.reverse()
            ip_reversed = '.'.join(ip_reversed)
            ip = ip_reversed

        if not self.ip.is_valid(ip):
            return None

        return ip

    def __value_to_phone(self, value):
        """
        Transform a DNS entry to a E.164 phone number
        :param value: The DNS entry
        :type value: str
        :return: The phone number or None
        :rtype str | None
        """
        match = self.re_e164.match(value)

        if match is None:
            return None

        number = match.group('number')

        number = number.replace('.', '') # Remove dot
        number = number[::-1] # Reverse order

        return  number

    def __discover_ip_address(self, value):
        """
        Discover a DNS entry with an ip address
        :param value: The DNS entry
        :type value: str
        :return: True if the value is an ip address, False otherwise
        :rtype: True | False
        """
        ip_address = self.__value_to_ip_address(value)
        if ip_address is None:
            return False

        self.ip.add_value(ip_address)

        return True

    def __discover_phone(self, value):
        """
        Discover a DNS entry with a phone number
        :param value: The DNS entry
        :type value: str
        :return: True if the value is an phone number, False otherwise
        :rtype: True | False
        """
        number = self.__value_to_phone(value)

        if number is None:
            return False

        self.phone.add_value(number)

        return True

    def __discover_domain(self, value):
        """
        Discover a DNS entry with a domain name
        :param value: The DNS entry
        :type value: str
        :return: True if the value is a domain name, False otherwise
        :rtype: True | False
        """
        if value.endswith('.'):
            value = value[:-1] # remove the last dot
        if self.domain.is_valid(value):
            self.domain.add_value(value, False)
            return True
        return False

    def __discover_name(self, value):
        """
        Discover DNS entry with a host name
        :param value: The DNS entry
        :type: value: str
        :return True if the value is a name, False otherwise
        :rtype: True | False
        """
        if value.endswith('.'):
            value = value[:-1] # remove the last dot
        if self.app.manager.data.get_data('name').is_valid(value):
            self.app.manager.data.get_data('name').add_value(value, False)
            return True
        return False

    def __anonymize_ip_address(self, value):
        """
        Anonymize a DNS entry with an IP address
        :param value: The DNS entry
        :type value: str
        :return: The replacement value or None
        :rtype: str | None
        """
        ip_address = self.__value_to_ip_address(value)

        if ip_address is None:
            return None

        ip_address = self.ip.get_replacement(ip_address)

        # Reverse byte to the reverse order for PTR
        ip_address = ip_address.split('.')
        ip_address.reverse()
        ip_address = '.'.join(ip_address)

        replacement = "{}.in-addr.arpa".format(ip_address)

        if value.endswith('.'):
            replacement += '.'

        return replacement

    def __anonymize_phone(self, value):
        """
        Anonymize a DNS entry with an E.164 phone number
        :param value: The DNS entry
        :type value: str
        :return: The replacement value or None
        :rtype: str | None
        """
        number = self.__value_to_phone(value)

        if number is None:
            return None

        number = self.phone.get_replacement(number)

        # E.164 to ENUM format
        number = number[::-1] # Reverse order
        number = list(number) # Split char to list
        number = '.'.join(number)

        replacement = "{}.e164.arpa".format(number)

        if value.endswith('.'):
            replacement += '.'

        return  replacement

    def __anonymize_domain(self, value):
        """
        Anonymize a DNS entry with a domain name
        :param value: The DNS entry
        :type value: str
        :return: The replacement value or None
        :type: str | None
        """
        if value.endswith('.'):
            value = value[:-1] # remove the last dot
        if self.domain.is_valid(value):
            return self.domain.get_replacement(value)
        return None

    def __anonymize_name(self, value):
        """
        Anonymize DNS entry with a host name
        :param value: The DNS entry
        :type: value: str
        :return: The replacement value or None
        :type: str | None
        """
        if value.endswith('.'):
            value = value[:-1] # remove the last dot
        if self.app.manager.data.get_data('name').is_valid(value):
            return self.app.manager.data.get_data('name').get_replacement(value)
        return None


