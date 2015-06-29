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
from collections import OrderedDict

from random import randint
import re

from sirano.data import Data
from sirano.utils import str_or_none


class PhoneData(Data):
    """Phone number Data plugin"""

    name = 'phone'

    re_phone = re.compile(r"^([#\*\+0-9]+)$")
    """Regex with authorized char for a phone number"""

    re_phone_find_format = r"(?:^|[^a-z0-9\.\-]){}(?:[^a-z0-9\.\-]|$)"
    """String of regular expression to find phone number in string"""

    def __init__(self, app):
        super(PhoneData, self).__init__(app)

        self.formats = None
        """
        Number formats in regular expression
        :type: list(str)
        """

        self.codes = dict()
        """
        Code with replacement values separated by number length
        :type: dict[int, dict[str, str]]
        """

        self.numbers = None
        """
        Number with replacement values
        :type: dict[str, str]
        """

    def _get_replacement(self, value):

        for a_format in self.formats:
            match = a_format.match(value)
            if match is not None:
                prefix = match.group(1)
                number = match.group(2)
                replacement = self.numbers.get(number, None)
                return prefix + replacement

        self.app.log.error("data:phone: Replacement value not found for '%s'", value)
        return None

    def post_load(self, ordereddict=None):
        self.numbers = self.link_data('numbers', dict)
        self.__post_load_codes()
        self.__post_load_formats()

    def pre_save(self):
        if 'codes' not in self.data:
            self.data['codes'] = dict()

        for length, codes in self.codes.items():
            codes = dict(codes)
            self.data['codes'][length] = codes

            for code, replacement in codes.items():
                self.data_report_value('code',code, replacement)

        for value, replacement in self.numbers.items():
            self.data_report_value('number',value, replacement)

    def process(self):
        self.__discover_code()
        self.__anonymise_code()
        self.__anonymise_number()

    def is_valid(self, value):
        if not isinstance(value, str):
            return False
        if self.re_phone.match(value) is None:
            self.app.log.debug("sirano:data:phone: Regex not match for value = '{}'".format(value))
            return False

        for a_format in self.formats:
            if a_format.match(value) is not None:
                return True

        return False

    def get_number_of_values(self):
        return len(self.numbers)

    def has_replacement(self, replacement):
        for a_format in self.formats:
            match = a_format.match(replacement)
            if match is not None:
                number = match.group(2)
                return number in self.numbers.values()
        return False

    def has_value(self, value):
        return self.numbers.has_key(value)

    def _add_value(self, value):
        for a_format in self.formats:
            match = a_format.match(value)
            if match is not None:
                number = match.group(2)
                if number not in self.numbers:
                    self.numbers[number] = None
                    return True
        return True

    def _find_values(self, string):
        values = list()
        for a_format in self.conf.get('formats', list()):
            re_format = re.compile(self.re_phone_find_format.format(a_format), re.IGNORECASE)
            founds = re_format.findall(string)
            for number in founds:
                number = ''.join(number)
                if self.is_valid(number):
                    values.append(number)
        return values

    def __post_load_formats(self):
        """
        Get internal representation of formats
        :return: List of compiled regular expression
        :rtype: list[re]
        """
        self.formats = list()
        for a_format in self.conf.get('formats', list()):
            self.formats.append(re.compile('^' + a_format + '$'))

    def __post_load_codes(self):
        """
        Generate the internal representation of codes
        """
        for length, conf_codes in self.data.setdefault('codes', dict()).items():
            # Convert key value to string or keep None if None
            conf_codes = dict(map(lambda (k,v): (str_or_none(k), str_or_none(v)), conf_codes.items()))
            codes = OrderedDict(conf_codes)
            self.codes[length] = codes

        self.__sort_codes()

    def __get_lcm_number(self, number):
        """
        Get longest code match for the specified number
        :param number: The number
        :type number: str
        :return: The codes or None if no one is found
        :rtype: str
        """
        codes = self.codes.setdefault(len(number), None)

        if codes is None:
            return None

        for code in codes.keys():
            if number.startswith(code):
                return code

        return None

    def __get_lcm_replacement(self, number, length=None):
        """
        Get the replacement value for a code from the specified length or the number length
        :param length: The length (optionnal)
        :type length: int
        :return: The replacement code or None if not found
        :rtype: str | None
        """
        if length is None:
            length = len(number)

        codes = self.codes.setdefault(length, dict())

        for code, replacement in codes.items():
            if number.startswith(code) and replacement is not None:
                return replacement
        return None

    def __discover_code(self):
        """
        Creates code if not already exists for an existent number
        """
        for number, replacement in self.numbers.items():
            length = len(number)
            if length <= 3:
                continue

            if self.__get_lcm_number(number) is None:
                code = number[:-3] # Remove the 3 last digit
                if length not in self.codes or self.codes[length] is None:
                    self.codes[length] = OrderedDict()
                self.codes[length][code] = None

        self.__sort_codes()

    def __sort_codes(self):
        """
        For each length sort codes by length (longest before)
        """
        for length, codes in self.codes.items():
            codes = OrderedDict(sorted(codes.items(), key=lambda code: len(code[0]), reverse=True))
            self.codes[length] = codes

    def __anonymise_code(self):
        """
        Creates replacement values for all codes
        """
        for lenght, codes in self.codes.items():
            for code, replacement in reversed(codes.items()):
                self.data_report_processed('code', 'number')
                if replacement is None:
                    try:
                        supercode = self.__get_lcm_replacement(code, lenght)
                        while range(100000): # Avoid infinite loop
                            if supercode is None:
                                rand_code = self.__rand_str_number(len(code))
                            else:
                                rand_code = supercode + self.__rand_str_number(len(code) - len(rand_code))

                            if not rand_code.startswith('0') and rand_code not in codes.values():
                                codes[code] = rand_code
                                break
                        self.data_report_processed('code', 'processed')
                    except Exception as e:
                        self.data_report_processed('code', 'error')
                        self.app.log.error("sirano:data:phone: Fail to generate a replacement value, code='{}',"
                                           "exception='{}', message='{}'".format(code, type(e), e.message))
                        raise

    def __anonymise_number(self):
        """
        Creates replacement values for all numbers
        """
        for number, replacement in self.numbers.items():
            self.data_report_processed('number', 'number')
            if replacement is None:
                try:
                    code = self.__get_lcm_replacement(number)
                    replacement = code + number[len(code):]
                    self.numbers[number] = replacement
                    self.data_report_processed('number', 'processed')
                except Exception as e:
                    self.data_report_processed('number', 'error')
                    self.app.log.error("sirano:data:phone: Fail to generate a replacement value, number='{}',"
                                           "exception='{}', message='{}'".format(number, type(e), e.message))
                    raise

    @staticmethod
    def __rand_str_number(length):
        """
        Randomize digit of a number
        :param length: The length
        :type length: str
        :return: The randomized number
        :type: str
        """
        rand_number = ''
        for _ in range(length):
            rand_number += str(randint(0, 9))
        return rand_number


