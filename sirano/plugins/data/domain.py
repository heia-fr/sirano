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
from sirano.exception import ValueNotFoundException
from sirano.utils import word_generator, word_generate

import re

from sirano.data import Data
from tld import get_tld


class DomainData(Data):
    """
    Domain Data plugin
    """

    name = 'domain'

    re_domain = re.compile(r"^((?:[A-Z0-9_](?:[A-Z0-9\-_]{0,61}[A-Z0-9])?\.){1,126}[A-Z]{2,6})$", re.IGNORECASE)
    """The regular expression to match a domain name"""

    re_domain_find = re.compile(r"((?:(?:[A-Z0-9\-_]{0,63})\.){2,127})", re.IGNORECASE)
    """The regular expression for finding a domain name"""

    def __init__(self, app):
        super(DomainData, self).__init__(app)

        self.domains = None
        """
        Domain names with replacement values
        :type: dict[str, str]
        """

        self.tlds = self.conf.get('tlds', list())
        """
        Top level domains
        :type: list[str]
        """

        self.exclusion = set()
        """
        Domain to not anonymize
        :type: set[str]
        """

        self.special_char = list()
        """
        Char to preserve during anonymization
        :type: list[str]
        """

    def post_load(self):
        self.domains = self.link_data('domains', dict)
        self.post_load_exclusion()
        self.post_load_special_char()

    def process(self):
        for domain, replacement in self.domains.items():
            self.data_report_processed('domain', 'number')
            if replacement is None:
                if domain in self.exclusion:
                    self.domains[domain] = domain
                else:
                    try:
                        self.__process_domain(domain)
                    except Exception as e:
                        self.data_report_processed('domain', 'error')
                        self.app.log.error(
                            "data:domain: Fail to process domain='{}', exception='{}', message='{}'".format(
                                domain, type(e), e.message
                            ))
                        raise
                self.data_report_processed('domain', 'processed')

    def is_valid(self, value):

        if not isinstance(value, str):
            return False

        # Check if it is not an IP address to avoid confusion
        if self.app.manager.data.get_data('ip').is_valid(value):
            return False

        # Check if the value ends with a TLD
        if (get_tld('http://' + value, fail_silently=True) is None) and (self.__tld_exist(value) is False):
            return False

        return self.re_domain.match(value) is not None

    def get_number_of_values(self):
        return len(self.domains)

    def pre_save(self):
        for value, replacement in self.domains.items():
            self.data_report_value('domain', value, replacement)

    def has_value(self, value):
        return value in self.domains

    def has_replacement(self, replacement):
        return replacement in self.domains.values()

    def _find_values(self, string):
        founds = self.re_domain_find.findall(string)
        values = filter(lambda v: self.is_valid(v), founds)
        return values

    def _add_value(self, value):
        if value not in self.domains:
            self.domains[value] = None
            return True
        return False

    def _get_replacement(self, value):

        r = self.domains.get(value, None)

        if r is None:
            raise ValueNotFoundException(
                "Replacement value not found, data = '{}', value = {}".format(self.name, value))

        return r

    def __tld_exist(self, domain):
        """
        Check if domain has an existent TLD in local list
        :param domain: the domain to check
        :type domain: str
        :return: True if exist, else False
        :rtype bool
        """
        for tld in self.tlds:
            if domain.endswith('.' + tld):
                return True

        return False

    def __process_domain(self, domain):
        """
        Process domain creates replacement values
        :param domain: The domain
        :type domain: str
        :return: Generator with domain level
        :rtype: list[str]
        """
        domain_split = domain.split('.')
        domain_split.reverse()
        domain_level = ''
        replacement_level = ''

        for index, label in enumerate(domain_split):
            if index != 0:
                domain_level = '{}.{}'.format(label, domain_level)
            else:
                domain_level = label

            replacement = self.domains.get(domain_level, None)
            if replacement is not None:
                replacement_level = replacement
            else:
                for replacement_label in self.__generate_random_label(label):
                    if index != 0:
                        replacement_level = '{}.{}'.format(replacement_label, replacement_level)
                    else:
                        replacement_level = replacement_label

                    if replacement_level not in self.domains.keys():
                        break
                self.domains[domain_level] = replacement_level

    def post_load_exclusion(self):
        """
        Called by post_load() to load internal representation of exception
        """
        exception = self.conf.get('exclusion')
        if isinstance(exception, list):
            for domain in exception:
                self.exclusion.add(domain)

    def __generate_random_label(self, label):
        """
        Generate random label and preserve the special char at same position
        :param label: The label
        :type label: str
        :return: The anonmyized label
        :rtype: list[str]
        """
        while True:
            new_label = label
            label_split = self.__split_label(label)
            for sublabel in label_split:
                new_label = new_label.replace(sublabel, word_generate(len(sublabel)))
            yield new_label

    def __split_label(self, label):
        """
        Split a name based on special char
        :param label: The name
        :type label: str
        :return: The list of name
        :type: list[str]
        """
        regex = '|'.join(map(re.escape, self.special_char))
        return re.split(regex, label)

    def post_load_special_char(self):
        """
        Called by post_load() to load internal representation of special_char
        """
        special_char = self.conf.get('special-char')
        if isinstance(special_char, list):
            for sc in special_char:
                self.special_char.append(sc)

