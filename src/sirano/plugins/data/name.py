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


from sirano.data import Data
from sirano.utils import word_generate


class NameData(Data):
    """Name Data plugin"""

    name = 'name'

    re_email_find = re.compile(r"([A-Z0-9._%+-]{2,})(?:@(?:[A-Z0-9.-]+\.[A-Z]{2,4}))", re.IGNORECASE)
    """Regular expression to find name in email addresses"""

    def __init__(self, app):
        super(NameData, self).__init__(app)

        self.names = None
        """
        Names with replacement values
        :type: dict[str, str]
        """

        self.special_char = None
        """
        Special characters
        :type: list[str]
        """

        self.exclusion = set()
        """
        Name to not anonymize
        :type: set[str]
        """

    def _add_value(self, value):
        value = value.lower()
        if value not in self.names:
            self.names[value] = None
            return True
        return False

    def process(self):
        for name, replacement in self.names.items():
            self.data_report_processed('name', 'number')
            if replacement is None:
                if name in self.exclusion:
                    self.names[name] = name
                else:
                    try:
                        replacement = self.__generate_name(name)
                        self.names[name] = replacement
                    except Exception as e:
                        self.data_report_processed('name', 'error')
                        self.app.log.error("sirano:data:name: Fail to generation a replacement value, name='{}',"
                                           "exception='{}', message='{}'".format(name, type(e), e.message))
                        raise
                self.data_report_processed('name', 'processed')

    def post_load(self):
        self.names = self.link_data('names', dict)
        self.special_char = self.conf.get('special-char', list())
        self.__post_load_exclusion()

    def _get_replacement(self, value):
        value = value.lower()
        r = self.names.get(value, None)
        if r is None:
            self.app.log.error("data:name: Replacement value not found for '%s'", value)
            return ''
        return r

    def has_replacement(self, replacement):
        replacement = replacement.lower()
        return replacement in self.names.values()

    def has_value(self, value):
        value = value.lower()
        return self.names.has_key(value)

    def is_valid(self, value):
        d = self.app.manager.data

        # Check if it is not an phone numbers, ip address or domain name to avoid confusion
        if d.get_data('phone').is_valid(value) or d.get_data('domain').is_valid(value) or d.get_data('ip').is_valid(
                value):
            return False
        return True

    def get_number_of_values(self):
        return len(self.names)

    def pre_save(self):
        self.data['names'] = self.names
        for value, replacement in self.names.items():
            self.data_report_value('name',value, replacement)
        self.names = dict(self.names)

    def _find_values(self, a_string):
        values = self.re_email_find.findall(a_string)
        values = filter(lambda v: self.is_valid(v), values)

        for name in self.names.keys():
            if name in a_string:
                values.append(name)
        return values

    def __split_name(self, name):
        """
        Split a name based on special char
        :param name: The name
        :type name: str
        :return: The list of name
        :type: list[str]
        """
        regex = '|'.join(map(re.escape, self.special_char))
        return re.split(regex, name)

    def __generate_name(self, name):
        """
        Generate a random name and keep special char
        :param name: The name
        :type name: str
        :return: The name generator
        :rtype: list[str]
        """
        name_split = self.__split_name(name)
        while True:
            replacement = name
            for subname in name_split:
                word = word_generate(len(subname))
                replacement = replacement.replace(subname, word, 1)

            if replacement not in self.names.keys():
                return replacement

    def __post_load_exclusion(self):
        """
        Called by post_load() to load internal representation of exception
        """
        exception = self.conf.get('exclusion')
        if isinstance(exception, list):
            for name in exception:
                self.exclusion.add(name)
