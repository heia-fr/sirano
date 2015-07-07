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

from collections import Counter
import os.path
import binascii
from hexdump import restore

import magic
import re
from scapy.layers.inet import IP
from sirano.file import File



class TextFile(File):

    name = 'text'

    re_hexdump = re.compile(r"([a-f0-9]+:?\s{1,2}[a-f0-9]{2}(?:\s{1,2}[a-f0-9\s]{2}){15}\s+.{16})", re.IGNORECASE)
    """
    The regular expression to find hexdump line
    """


    def __init__(self, app, a_file):
        super(TextFile, self).__init__(app, a_file)
        self.app.log.info("Filetype 'text' initialized")

        self.hexdump = False
        self.hexdump_lines = list()

    def __discover_file_structure(self):
        re_word = re.compile(r"[\s'\"@]+")
        global_counter = Counter()

        path = os.path.join(self.app.project.input, self.file)

        with open(path) as a_file:

            counter = Counter()

            for line in a_file:
                words = re_word.split(line)

                for word in words:
                    if len(word) >= 2:
                        counter[word] += 1
                        global_counter[word] += 1

        # print global_counter.most_common(100)
        # print len(global_counter)


    def discover(self):

        self.__discover_file_structure()

        action = self.app.manager.action.get_action('auto')

        a_file = os.path.join(self.app.project.input, self.file)

        with open(a_file, 'r') as f:
            for line in f:
                line = line.replace('\r', '').replace('\n', '')
                if self.re_hexdump.search(line) is None:
                    action.discover(line)

    def __replace(self, file_out):
        action = self.app.manager.action.get_action('auto')

        file_in = os.path.join(self.app.project.input, self.file)

        with open(file_in, 'r') as f_in:
            with open(file_out, 'w') as f_out:
                for line in f_in:
                    line = line.replace('\r', '')

                    if self.__process_hexdump(f_out, line):
                        continue
                    else:
                        new_line = action.anonymize(line)
                        f_out.write(new_line)


    def anonymize(self):
        self.__replace(os.path.join(self.app.project.output, self.file))

    def validate(self):
        self.app.manager.data.set_clean_mode_all(True)
        root, ext = os.path.splitext(self.file)
        filename = root + '.clean' + ext
        self.__replace(os.path.join(self.app.project.validation, filename))
        self.app.manager.data.set_clean_mode_all(False)

    @classmethod
    def is_compatible(cls, path):
        typedesc = magic.from_file(path)
        return str(typedesc).startswith("ASCII text")

    def add_file(self, filename):
        super(TextFile, self).add_file(filename)

    def __process_hexdump(self, f_out, line):

        search = self.re_hexdump.search(line)

        if search is not None:
            line = line.replace(search.group(0), '--> hex dump removed by Sirano <--')
            f_out.write(line)

        # Just remove hexdump for this moment
        # if is_match:
        #     self.hexdump_lines.append(line)
        # else:
        #     if self.hexdump: # and (not is_match)
        #         dump = ''.join(self.hexdump_lines)
        #         packet = self.__hexdump_to_packet(dump)
        #
        #         if packet is not None:
        #             if Raw in packet:
        #                 del(packet[Raw])
        #             self.app.packet.anonymize(packet)
        #             dump = hexdump(str(packet), result='return')
        #             if dump is not None:
        #                 f_out.write(dump + '\n')
        #         self.hexdump_lines = list()
        #
        # self.hexdump = is_match
        return search is not None

    def __contain_hexdump(self, path):
        """
        Check if a file contain some hexdump
        :param path: The path of the file
        :type path: str
        :return: True if the file contain some hexdump, False otherwise
        :rtype True | False
        """
        with open(path) as a_file:
            for line in a_file:
                line = line.replace('\r', '') # Compatibility with windows file
                match = self.re_hexdump.match(line)
                if match: # is not None
                    return True

        return False

    @staticmethod
    def __hexdump_to_packet(a_hexdump):
        """
        Tranformt a hexdump to a packet if is it valid
        :param a_hexdump: The hexdump
        :type a_hexdump: str
        :return: The scapy Packet or None if the packet is not valid
        :rtype Packet | None
        """
        raw = restore(a_hexdump)

        if raw.startswith(binascii.unhexlify('0004')):
            return IP(raw)
        else:
            return None

