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
from scapy.packet import Packet, NoPayload
from scapy.utils import PcapWriter, PcapReader
from enum import Enum
from sirano.app import Phase

from sirano.exception import ExplicitDropException, ImplicitDropException
from sirano.file import File

class _LayerStats(object):
    def __init__(self):
        self.dropped = 0
        self.anonymized = 0

    def __str__(self):
        return 'dropped = {}, anonymized = {}'.format(self.dropped, self.anonymized)

class _PCAPStats(object):
    def __init__(self, app, name):
        """
        Statistic

        Contain all statistic for the report
        """
        self.name = name
        self.app = app
        self.layers = defaultdict(_LayerStats)
        self.dropped = 0
        self.anonymized = 0

    def packet_dropped(self, packet):
        self.dropped += 1
        layer = packet
        while not isinstance(layer, NoPayload):
            layer_name = layer.__class__.__name__
            self.layers[layer_name].dropped += 1
            layer = layer.payload  # Get next layer

    def packet_anonymised(self, packet):
        self.anonymized += 1
        layer = packet
        while not isinstance(layer, NoPayload):
            layer_name = layer.__class__.__name__
            self.layers[layer_name].anonymized += 1
            layer = layer.payload  # Get next layer

    def __str__(self):
        text = "PCAP file\n" \
              "---------\n" \
              "packet: dropped = {}, anonymized = {}, total = {}\n".format(self.dropped, self.anonymized, self.total)
        for layer, stats in self.layers.iteritems():
            text += "'{}' : {}\n".format(layer, stats)

        return text

    @property
    def total(self):
        return self.dropped + self.anonymized

    def save(self):
        """
        Save the statistic to a file
        """

        path = os.path.join(self.app.project.report, os.path.splitext(self.name)[0] + '.txt')

        try:
            os.makedirs(self.app.project.report)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(self.app.project.report):
                pass
            else:
                raise

        filepath = open(path, 'w')

        filepath.write(self.__str__())
        filepath.close()


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

    def __init__(self, app, file):
        super(PCAPFile, self).__init__(app, file)

        self.layers = defaultdict(lambda: _LayerAction(app))
        self.app.log.info("Filetype 'pcap' initialized")

    def __process_packets(self, packets, out_writer, drop_writer, validation_file, stat):
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
                            validation = validation.replace('\n', '\n  ') # Indent
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
                    stat.packet_dropped(packet)

                else:
                    if self.app.phase is Phase.phase_3:
                        out_writer.write(packet)
                    stat.packet_anonymised(packet)

            except Exception as e:
                self.app.log.critical("Unexpected error: id = '{}', {}, {}".format(packet_id, e.message,
                                                                                   packet.summary()))

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
            path = os.path.join(self.app.project.validation, os.path.splitext(name)[0] + '.txt')

            try:
                os.makedirs(self.app.project.validation)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(self.app.project.validation):
                    pass
                else:
                    raise

            validation_file = open(path, 'w')

        stat = _PCAPStats(self.app, name)

        try:
            self.__process_packets(packets,
                                   out_writer,
                                   drop_writer,
                                   validation_file,
                                   stat)
        except Exception as e:
            self.app.log.critical("file:pacp: Unexpected error: " + str(e))
        else:
            stat.save()
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
        self.__process_file(self.file)

    @classmethod
    def is_compatible(cls, path):
        typedesc = magic.from_file(path)
        return str(typedesc).startswith("tcpdump capture file")

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