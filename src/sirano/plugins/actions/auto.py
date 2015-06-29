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


from sirano.action import Action


class AutoAction(Action):
    """
    Action plugin for unknown data structures (automatic)
    """

    name = "auto"

    def __init__(self, app):
        super(AutoAction, self).__init__(app)

    def __discover_generic(self, string, data):
        """
        Generic method for the discover process
        :param string: the string to discover
        :type string: str
        :param data: the name of the data manager to use
        :type data: str
        """
        # :type Data
        data = self.app.manager.data.get_data(data)
        # :type list[str]
        values = data.find_values(string)
        # Remove duplicates
        values = set(values)
        for value in values:
            data.add_value(value, False)

    def __anonymize_generic(self, string, data):
        """
        Generic method for the anonymize process
        :param string: the string to anonymize
        :type string: str
        :param data: the name of the data manager to use
        :type data: str
        :return The anonymized value
        :rtype str
        """
        # :type Data
        data = self.app.manager.data.get_data(data)
        # :type list[str]
        values = data.find_values(string)
        values.sort(key=len, reverse=True) # Replace the longest value first
        for value in values:
            replacement = data.get_replacement(value)
            string = string.replace(value, replacement)
        return string

    def discover(self, value):
        self.__discover_generic(value, 'ip')
        self.__discover_generic(value, 'domain')
        self.__discover_generic(value, 'mac')
        self.__discover_generic(value, 'phone')
        self.__discover_generic(value, 'name')

    def anonymize(self, value):
        value = self.__anonymize_generic(value, 'ip')
        value = self.__anonymize_generic(value, 'domain')
        value = self.__anonymize_generic(value, 'mac')
        value = self.__anonymize_generic(value, 'phone')
        value = self.__anonymize_generic(value, 'name')
        return value

