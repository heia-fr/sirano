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

from random import randint, shuffle
import re

from sirano.data import Data
from sirano.exception import ValueNotFoundException
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

        self.formats = list()
        """
        Number formats in regular expression
        :type: list(str)
        """

        self.codes = dict()
        """
        Code with replacement code
        Must be ordered by length with an OrderedDict (longest before)
        :type: dict[str, str]
        """

        self.numbers = dict()
        """
        Number with replacement values
        :type: dict[str, str]
        """

        self.digit_preserved = 3
        """
        Number of preserved digit by default
        :type: int
        """

        self.exclusion = set()
        """
        Number to not anonymize
        :type: set[str]
        """

    def _get_replacement(self, value):

        for a_format in self.formats:
            match = a_format.match(value)
            if match is not None:
                prefix = match.group(1)
                number = match.group(2)
                replacement = self.numbers.get(number, None)
                return prefix + replacement

        raise ValueNotFoundException("Replacement value not found, data = '{}', value = {}".format(self.name, value))

    def post_load(self, ordereddict=None):
        self.digit_preserved = self.conf.get('digit-preserved', self.digit_preserved)
        self.__post_load_exclusion()
        self.__post_load_numbers()
        self.__post_load_codes()
        self.__post_load_formats()

    def pre_save(self):
        self.__pre_save_codes()
        self.__pre_save_numbers()

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

    def __post_load_exclusion(self):
        """
        Called by post_load() to load internal representation of exclusion
        """
        exclusion = self.conf.get('exclusion')
        if isinstance(exclusion, list):
            for number in exclusion:
                self.exclusion.add(str(number))

    def __post_load_formats(self):
        """
        Called by post_load() to load internal representation of formats
        """
        formats = self.conf.get('formats')
        if isinstance(formats,list):
            for a_format in formats:
                self.formats.append(re.compile('^' + a_format + '$'))

    def __post_load_codes(self):
        """
        Called by post_load() to load internal representation of codes
        """
        codes = self.data.get('codes')
        if isinstance(codes, dict):
            for code, replacement in codes.items():
                code = str(code).upper()
                if replacement is not None:
                    replacement = str(replacement).upper()
                self.codes[code] = replacement
            self.__sort_codes()

    def __post_load_numbers(self):
        """
        Called by post_load() to load internal representation of numbers
        """
        numbers = self.data.get('numbers')
        if not isinstance(numbers, dict):
            numbers = dict()
        for number, replacement in numbers.items():
            self.numbers[str(number)] = str_or_none(replacement)

    def __get_lcm_number(self, number):
        """
        Get longest code match for the specified number
        :param number: The number
        :type number: str
        :return: The codes or None if no one is found
        :rtype: str
        """
        length = len(number)
        for code in self.codes.keys():
            if len(code) == length and number.startswith(code.replace('X', '')):
                return code
        return None

    def __get_lcm_replacement(self, number):
        """
        Get the replacement code from another code or a number with the longest match
        :param number: The code or the number
        :type number: str
        :return: The replacement code or None if not found
        :rtype: str | None
        """
        length = len(number)
        for code, replacement in self.codes.items():
            if (replacement is not None) and number.startswith(code.replace('X', '')):
                return replacement
        return None

    def __discover_code(self):
        """
        Creates code if not already exists for an existent number
        """
        for number, replacement in self.numbers.items():
            length = len(number)
            if length <= self.digit_preserved:
                continue
            if (number not in self.exclusion) and (self.__get_lcm_number(number) is None):
                code = number[:-self.digit_preserved] # Remove the preserved digit
                code += 'X' * self.digit_preserved
                self.codes[code] = None

        self.__sort_codes()

    def __sort_codes(self):
        """
        For each sort codes by length (longest before)
        """
        self.codes = OrderedDict(sorted(self.codes.items(), key=lambda x: len(x[0].replace('X', '')), reverse=True))

    def __anonymise_code(self):
        """
        Creates replacement values for all codes
        """
        for code, replacement in reversed(self.codes.items()):
            self.data_report_processed('code', 'number')
            if replacement is None:
                try:
                    supercode = self.__get_lcm_replacement(code)
                    has_supercode = supercode is not None
                    i = 0
                    while True:
                        if has_supercode:
                            rand_code = supercode.replace('X', '') + self.__rand_str_number(len(code.replace('X', '')) - len(supercode.replace('X', '')))
                        else:
                            rand_code = self.__rand_str_number(len(code.replace('X', '')))
                        rand_code += 'X' * (len(code) - len(code.replace('X', '')))
                        if rand_code not in self.codes.values():
                            self.codes[code] = rand_code
                            break
                        i +=1
                        if i > 100000000:
                            self.app.log.error("Fail to generate code replacement value, code = '{}'".format(code))
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
                if number in self.exclusion:
                    self.numbers[number] = number
                else:
                    try:
                        code = self.__get_lcm_replacement(number)
                        replacement = code.replace('X', '') + number[len(code.replace('X', '')):]
                        self.numbers[number] = replacement
                    except Exception as e:
                        self.data_report_processed('number', 'error')
                        self.app.log.error("sirano:data:phone: Fail to generate a replacement value, number='{}',"
                                               "exception='{}', message='{}'".format(number, type(e), e.message))
                        raise
                self.data_report_processed('number', 'processed')

    @staticmethod
    def __rand_str_number(length):
        """
        Randomize digit of a number
        :param length: The length
        :type length: int
        :return: The randomized number
        :type: str
        """
        rand_number = list()
        for _ in range(length):
            rand_number.append(str(randint(0, 9)))
        shuffle(rand_number) # More random
        return ''.join(rand_number)

    def __pre_save_codes(self):
        """
        Called by pre_save() to prepare codes for saving
        """
        if not isinstance(self.data.get('codes'), dict):
            self.data['codes'] = dict()
        for code, replacement in self.codes.items():
            self.data['codes'][code] = replacement
            self.data_report_value('code',code, replacement)

    def __pre_save_numbers(self):
        """
        Called by pre_save() to prepare numbers for saving
        """
        if not isinstance(self.data.get('numbers'), dict):
            self.data['numbers'] = dict()
        for number, replacement in self.numbers.items():
            self.data['numbers'][number] = replacement
            self.data_report_value('number',number, replacement)


