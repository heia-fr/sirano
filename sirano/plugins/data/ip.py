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

from collections import OrderedDict, defaultdict

import random

import re
from math import ceil

from netaddr import IPNetwork, IPAddress
from sirano.data import Data
from sirano.exception import ValueNotFoundException


class IPData(Data):
    """IP Data plugin"""

    name = 'ip'

    re_ip_find = re.compile(r"(?:(?:(?:\d{1,3}\.){3}\d{1,3}\.in-addr\.arpa)|((?:\d{1,3}\.){3}\d{1,3}))")
    """
    Simplified regular expression to find IP addresses
    Force to not match PTR record
    """

    re_ip = re.compile(r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$")
    """The regular expression for a ip address"""

    def __init__(self, app):
        super(IPData, self).__init__(app)
        self.hosts = dict()

        self.subnets = None
        """
        Dictionary with subnet and replacement sorted by prefix length (longest to shortest)
        :type dict[IPNetwork, IPNetwork]
        """

        self.blocks = self.__get_blocks()
        """
        Addresses blocks list
        :type list[IPNetwork]
        """

        self.exclusion = set()
        """
        IP addresses to not anonymize
        :type: set[str]
        """

    def post_load(self):
        self.hosts = self.link_data('hosts', dict)
        self.subnets = self.__get_subnets()
        self.__post_load_exclusion()

    def pre_save(self):
        self.__pre_save_hosts()
        self.__pre_save_subnets()

    def process(self):
        self.__discover_subnet()
        self.__process_subnets()
        self.__process_hosts()

    def clear(self):
        for k in self.hosts.keys():
            self.hosts[k] = ''

    def has_replacement(self, replacement):
        return replacement in self.hosts.values()

    def has_value(self, value):
        return value in self.hosts

    def _add_value(self, ip):
        if ip not in self.hosts:
            self.hosts[ip] = None
            return True
        return False

    def is_valid(self, value):
        """
        Check if an ip address is valid
        Please de not use the buggy function netaddr.valid_ipv4()
        :param value: The IP address to check
        :type value: str
        """
        return self.re_ip.match(value) is not None

    def get_number_of_values(self):
        return len(self.hosts)

    def _find_values(self, string):
        founds = self.re_ip_find.findall(string)
        values = filter(lambda v: self.is_valid(v), founds)
        return values

    def _get_replacement(self, value):
        r = self.hosts.get(value, None)

        if r is None:
            raise ValueNotFoundException("Replacement value not found, data = '{}', value = {}".format(
                self.name, value))

        return r

    def __get_subnets(self):
        """
        Generate the internal representation of subnets
        :return: the subnets
        :rtype dict[IPNetwork, IPAddress]
        """
        subnets = dict()

        for subnet, replacement in self.data.setdefault('subnets', dict()).items():
            try:
                subnet = IPNetwork(subnet)

                if replacement:  # is not None
                    replacement = IPNetwork(replacement)

                subnets[subnet] = replacement
            except Exception as e:
                self.app.log.error("{} : in 'ip.yml'".format(e))

        subnets = OrderedDict(sorted(subnets.items(), key=lambda network: network[0].prefixlen, reverse=True))

        return subnets

    def __pre_save_subnets(self):
        """ Transform subnets property to be serialized """
        subnets = dict()
        for subnet, replacement in self.subnets.items():
            if replacement:  # is not None
                replacement.prefixlen = subnet.prefixlen
                replacement = str(replacement)
            subnet = str(subnet)
            subnets[subnet] = replacement
            self.data_report_value('subnet', subnet, replacement)
        self.data['subnets'] = subnets

    def __process_subnets(self):
        for subnet, replacement in reversed(self.subnets.items()):  # iterate from the shortest prefix to the longest
            self.data_report_processed('subnet', 'number')
            if replacement is None:
                try:
                    replacement = self.__anonymize_subnet(subnet)
                    self.subnets[subnet] = replacement
                    self.data_report_processed('subnet', 'processed')
                except Exception as e:
                    self.data_report_processed('subnet', 'error')
                    self.app.log.error("sirano:data:ip: Fail to generate a replacement value, subnet='{}', "
                                       "exception='{}', message='{}".format(subnet, type(e), e.message))
                    raise

    def __process_hosts(self):
        for host, replacement in self.hosts.items():
            self.data_report_processed('host', 'number')
            if replacement is None or replacement == 'None':  # is None
                if host in self.exclusion:
                    self.hosts[host] = host
                else:
                    try:
                        replacement = self.__anonymize_host(IPAddress(host))
                        self.hosts[host] = str(replacement)
                    except Exception as e:
                        self.data_report_processed('host', 'error')
                        self.app.log.error("sirano:data:ip: Fail to generate a replacement value, host='{}', "
                                           "host='{}', exception='{}', message='{}'".format(host, type(e), e.message))
                        raise
                self.data_report_processed('host', 'processed')

    def __get_blocks(self):
        """
        Retrieve the blocks of addresses from the configuration and generate the internal representation
        :return: the blocks
        :rtype IPNetwork
        """
        blocks = list()
        for network in self.conf['blocks']:
            blocks.append(IPNetwork(network))
        # Sort by prefix length (longest to shortest)
        blocks = sorted(blocks, key=lambda x: x.prefixlen, reverse=True)
        return blocks

    @staticmethod
    def __round_down_prefix(prefix):
        """
        Round prefix down (shortest or the upper byte)
        :param prefix: the prefix to round
        :return: the new prefix
        """
        return prefix/8*8

    @staticmethod
    def __round_up_prefix(prefix):
        """
        Round prefix up (longest or the downer byte)
        :param prefix: the prefix to round
        :return: the new prefix
        """
        return int(ceil(prefix/8)*8)

    def __get_lpm_block(self, ip_address):
        """
        Get the longest prefix match for an IP address or network
        :param ip_address the ip address to lookup
        :type ip_address: IPAddress
        :return: the network of the block
        :rtype IPNetwork
        """
        for network in self.blocks:
            if ip_address in network:
                return network
        raise Exception("No block is found for the ip {}".format(ip_address))

    def __get_lpm_subnet_replacement(self, ip_address):
        """
        Get the replacement subnet for the longest prefix match with an IP address or network
        :param ip_address the ip address to lookup
        :type ip_address: IPAddress
        :return: the replacement subnet or None if not found
        :rtype IPNetwork | None
        """
        for subnet, replacement in self.subnets.items():
            if replacement and ip_address in subnet:
                return replacement
        return None

    def __is_subnet_exists_in_supernet(self, supernet):
        """
        Check if a replacement exists in subnet for the specified supernet
        :param supernet: The supernet
        :type supernet: IPNetwork
        :return: True if exists, False otherwise
        :rtype True | False
        """
        for subnet, replacement in self.subnets.items():
            if replacement and subnet in supernet:
                return True
        return False

    def __is_subnet_exists(self, host):
        """
        Check if subnet exists for the specified host
        :param host: The host to check
        :type host: IPAddress
        :return: True if exists, False otherwise
        :rtype True | False
        """
        for subnet in self.subnets.keys():
            if host in subnet:
                return True
        return False

    def __is_replacement_subnet_exists(self, subnet):
        """
        Check if the replacement subnet already exists

        :param subnet: The subnet
        :type subnet: IPNetwork
        :return: True if exists, False otherwise
        :rtype True | False
        """
        # TODO Optimize this search
        for replacement in self.subnets.values():
            if replacement == subnet:
                return True
        return False

    def __anonymize_host(self, host):
        """
        Anonymize a host adress keeping the same subnet or take /24 for the default subnet
        :param host: The host to anonymize
        :type host: IPAddress
        :return: The anonymized host
        :rtype: IPAddress
        """

        subnet = self.__get_lpm_subnet_replacement(host)

        if not subnet:  # is None
            self.app.log.error("Subnet not exist for host {}".format(host))
            raise Exception("Subnet not exist for host {}".format(host))

        prefixlen = subnet.prefixlen

        if prefixlen < 8:
            byte_to_anonymize = 0
            self.app.log.error("Impossible to anonymize the host, the prefix is too short, host = '{}', "
                               "subnet = '{}'".format(subnet, subnet))
        elif prefixlen < 16:
            byte_to_anonymize = 1
            self.app.log.warning("The anonymized host is not very secure, the subnet prefix is too short "
                                 "host = '{}', subnet = '{}'".format(host, subnet))
        elif prefixlen < 24:
            byte_to_anonymize = 2
        elif prefixlen < 32:
            byte_to_anonymize = 3
        else:  # prefixlen == 32
            byte_to_anonymize = 4

        subnet_bytes = str(subnet.network).split('.')
        host_bytes = str(host).split('.')

        for byte in range(byte_to_anonymize):
            host_bytes[byte] = subnet_bytes[byte]

        new_host = IPAddress('.'.join(host_bytes))

        return new_host

    def __discover_subnet(self):
        """
        Creates subnet with prefix /24 for IP that not match with an existent one
        """
        for host in self.hosts:
            if host in self.exclusion:
                continue

            host = IPAddress(host)

            if self.__is_subnet_exists(host):
                continue

            subnet = IPNetwork(host)
            subnet.prefixlen = 24

            # Remove the host part
            subnet = IPNetwork(subnet.network)
            subnet.prefixlen = 24

            self.subnets[subnet] = None

        self.subnets = OrderedDict(sorted(self.subnets.items(), key=lambda network: network[0].prefixlen, reverse=True))

    @staticmethod
    def __ip_address_to_bytes(ip_address):
        """
        Convert an IP adresse to an array of bytes
        :param ip_address: The IP address
        :type ip_address: IPAddress
        :return: The array of bytes
        :rtype: list[int]
        """
        return map(int, str(ip_address).split('.'))

    def __anonymize_subnet(self, subnet):
        """
        Anonymize a subnet address keeping the same block of addresses
        :param subnet: the network to anonymize
        :type subnet: IPNetwork
        :return: the anonymized network
        :rtype IPNetwork
        """

        if self.__is_subnet_exists_in_supernet(subnet):
            self.app.log.warning("The supernet is already anonymized for this subnet, it is anonymized but it lost the "
                                 "consistence with its supernet, subnet = '{}'".format(subnet))

        supernet = self.__get_lpm_subnet_replacement(subnet)
        if supernet is not None:
            supernet.prefixlen = self.__round_down_prefix(supernet.prefixlen)
        else:
            supernet = self.__get_lpm_block(subnet)

        bytes_len = map(len, str(subnet).split('.'))
        bytes_min = self.__ip_address_to_bytes(IPAddress(supernet.first))
        bytes_max = self.__ip_address_to_bytes(IPAddress(supernet.last))
        bytes_new = self.__ip_address_to_bytes(subnet.network)

        prefixlen = subnet.prefixlen

        if prefixlen < 8:
            byte_to_anonymize = 0
            self.app.log.error("Impossible to anonymize the subnet, the prefix is too short, subnet = '{}', "
                               "supernet = '{}'".format(subnet, supernet))
        elif prefixlen < 16:
            byte_to_anonymize = 1
            self.app.log.warning("The anonymized subnet is not very secure, the prefix is too short "
                                 "subnet = '{}', supernet = '{}'".format(subnet, supernet))
        elif prefixlen < 24:
            byte_to_anonymize = 2
        elif prefixlen < 32:
            byte_to_anonymize = 3
        else:  # prefixlen == 32
            byte_to_anonymize = 4

        bytes_rand = defaultdict(list)

        for byte in range(byte_to_anonymize):
            # Transform min and max byte for respecting the number of character
            byte_len = bytes_len[byte]
            byte_max = min(int('9' * byte_len), bytes_max[byte])  # The last byte that have the same char number
            byte_min = max(10 * (byte_len - 1), bytes_min[byte])  # The first byte that have the same char number

            # Prepare random number list for the byte
            bytes_rand[byte] = range(byte_min, byte_max + 1)
            random.shuffle(bytes_rand[byte])

        def replace_byte(a_byte):
            for byte_rand in bytes_rand[a_byte]:
                bytes_new[a_byte] = byte_rand
                new_subnet = replace_byte(a_byte + 1)
                if new_subnet is not None:
                    return new_subnet
            else:
                new_subnet = IPNetwork('{}/{}'.format('.'.join(map(str, bytes_new)), prefixlen))
                if not self.__is_replacement_subnet_exists(new_subnet):
                    return new_subnet
                else:
                    return None
        return replace_byte(0)

    def __pre_save_hosts(self):
        for value, replacement in self.hosts.items():
            self.data_report_value('host', value, replacement)

    def __post_load_exclusion(self):
        """
        Called by post_load() to load internal representation of exception
        """
        exception = self.conf.get('exclusion')
        if isinstance(exception, list):
            for ip in exception:
                self.exclusion.add(ip)






