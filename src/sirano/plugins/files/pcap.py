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

from collections import defaultdict
import os.path
import errno

import magic
from scapy.packet import Packet
from scapy.utils import PcapWriter, PcapReader
from enum import Enum
import subprocess
from sirano.app import Phase

from sirano.exception import ExplicitDropException, ImplicitDropException
from sirano.file import File


class _LayerActionEnum(Enum):
    implicit_drop = 0
    explicit_drop = 1
    implicit_pass = 2
    explicit_pass = 3


class _LayerAction(object):
    def __init__(self, app):
        self.other_fields = app.manager.action.get_action('implicit-drop')
        self.fields = defaultdict(lambda: self.other_fields)
        self.default = _LayerActionEnum.implicit_drop

    def add_action(self, field, action):
        self.fields[field] = action
        self.default = _LayerActionEnum.implicit_pass


class PCAPFile(File):
    name = 'pcap'

    def __init__(self, app, a_file):
        super(PCAPFile, self).__init__(app, a_file)
        self.validation_file_tshark = os.path.join(self.app.project.validation,
                                                   os.path.splitext(self.file)[0] + '.tshark.txt')
        self.layers = defaultdict(lambda: _LayerAction(app))
        self.app.log.info("Filetype 'pcap' initialized")

    def __process_packets(self, packets, out_writer, drop_writer, validation_file):
        """
        :type packets: list[Packet]
        :return A tuple with the number of packets anonymized and the number of packets dropped
        :rtype (int, int)
        """

        for index, packet in enumerate(packets):
            packet_id = index + 1  # packet id start with 1

            packet_backup = Packet(str(packet))
            packet_backup.time = packet.time

            try:
                try:
                    if self.app.phase is Phase.phase_1:
                        self.app.packet.discover(packet)
                    elif self.app.phase is Phase.phase_3:
                        self.app.packet.anonymize(packet)
                    elif self.app.phase is Phase.phase_4:
                        validation = self.app.packet.validate(packet)
                        if validation is not None:
                            validation_file.write("\n\nPacket id {}:\n  ".format(packet_id))
                            validation = validation.replace('\n', '\n  ')  # Indent
                            validation_file.write(validation)

                except Exception as e:
                    if isinstance(e, ExplicitDropException):
                        self.app.log.info("Packet explicitly dropped: id = '{}', {}, {}".format(packet_id, e.message,
                                                                                                packet.summary()))
                    elif isinstance(e, ImplicitDropException):
                        self.app.log.warning("Packet implicitly dropped: id = '{}', {}, {}".format(packet_id, e.message,
                                                                                                   packet.summary()))
                    else:
                        raise

                    if self.app.phase is Phase.phase_3:
                        drop_writer.write(packet_backup)

                else:
                    if self.app.phase is Phase.phase_3:
                        out_writer.write(packet)

            except Exception as e:
                self.app.log.critical("Unexpected error: id = '{}', exception = '{}', message = '{}', {}".format(
                    packet_id, type(e), e.message, packet.summary()))

    def __process_file(self, name):

        self.app.log.info("file:pcap: Start anonymization: File = '{}'".format(name))

        in_path = os.path.join(self.app.project.input, name)
        packets = PcapReader(in_path)

        out_writer = None
        drop_writer = None
        validation_file = None

        if self.app.phase is Phase.phase_3:
            out_path = os.path.join(self.app.project.output, name)
            drop_path = os.path.join(self.app.project.trash, name)

            # Remove files before append
            try:
                os.remove(out_path)
            except OSError:
                pass
            try:
                os.remove(drop_path)
            except OSError:
                pass

            out_writer = SiranoPcapWriter(out_path, append=True)
            drop_writer = SiranoPcapWriter(drop_path, append=True)

        elif self.app.phase is Phase.phase_4:
            path = os.path.join(self.app.project.validation, os.path.splitext(name)[0] + '.clean.txt')

            try:
                os.makedirs(self.app.project.validation)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(self.app.project.validation):
                    pass
                else:
                    raise

            validation_file = open(path, 'w')

        try:
            self.__process_packets(packets,
                                   out_writer,
                                   drop_writer,
                                   validation_file)
        except Exception as e:
            self.app.log.critical("file:pacp: Unexpected error: " + str(e))
        finally:
            if self.app.phase is Phase.phase_3:
                out_writer.close()
                drop_writer.close()

            elif self.app.phase is Phase.phase_4:
                validation_file.close()

    def discover(self):
        self.__process_file(self.file)

    def anonymize(self):
        self.__process_file(self.file)

    def validate(self):
        self.app.manager.data.clean_mode = True
        self.__process_file(self.file)
        self.app.manager.data.clean_mode = False
        self.__validate_create_tshark()
        self.__validate_check_tshark()

    @classmethod
    def is_compatible(cls, path):
        typedesc = magic.from_file(path)
        return str(typedesc).startswith("tcpdump capture file")

    def __validate_create_tshark(self):
        out_file = os.path.join(self.app.project.output, self.file)
        val_file = self.validation_file_tshark

        command = "tshark -r {} -V > {}".format(out_file, val_file)
        subprocess.call(command, shell=True)

    def __validate_check_tshark(self):
        values = defaultdict(list)
        with open(self.validation_file_tshark) as a_file:
            for line_number, line in enumerate(a_file):
                values_line = self.app.manager.data.find_values_all(line)
                for data, value in values_line.items():
                    value = map(lambda x: (line_number, x), value)
                    values[data].extend(value)

        values = dict(map(lambda (k, v): (k, set(v)), values.items()))

        for data_name, set_of_values in values.items():
            data = self.app.manager.data.get_data(data_name)
            for line_number, value in set_of_values:
                if not data.has_replacement(value):
                    lines = []
                    self.app.log.error(
                        "sirano:file:pcap: Validation error value is not replaced, files = '{}', line = '{}', "
                        "data = '{}', value = '{}'".format(self.file, line_number, data_name, value))

# noinspection PyClassicStyleClass
class SiranoPcapWriter(PcapWriter):
    def write(self, pkt):
        """
        Same than original implementation but write only one packet
        :param pkt: The packet to write
        :type pkt: Packet
        """
        if not self.header_present:
            self._write_header(pkt)
        if type(pkt) is str:
            self._write_packet(pkt)
        else:
            self._write_packet(pkt)
