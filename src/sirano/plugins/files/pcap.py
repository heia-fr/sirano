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
from scapy.utils import rdpcap, PcapWriter
from enum import Enum
from sirano.app import Phase

from sirano.exception import ExplicitDropException, ImplicitDropException
from sirano.file import File


class _LayerActionEnum(Enum):
    implicit_drop = 0
    explicit_drop = 1
    implicit_pass = 2
    explicit_pass = 3


class _Stat(object):
    def __init__(self, app, name):
        """
        Statistic

        Contain all statistic for the report
        """
        self.packets_anonymized = 0
        self.packets_dropped = 0
        self.name = name
        self.app = app

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

        filepath.write("{}\n"
                       "Anonymization report for PCAP file\n"
                       "{}\n"
                       "\n"
                       "Packets anonymized {:>10}\n"
                       "Packets dropped    {:>10}\n"
                       "=============================\n"
                       "Total packets      {:>10}\n".format("=" * 80,
                                                            "=" * 80,
                                                            self.packets_anonymized,
                                                            self.packets_dropped,
                                                            self.packets_total))
        filepath.close()

    @property
    def packets_total(self):
        return self.packets_anonymized + self.packets_dropped


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

    def __init__(self, app):
        super(PCAPFile, self).__init__(app)

        self.layers = defaultdict(lambda: _LayerAction(app))
        self.__load_config()

        self.app.log.info("Filetype 'pcap' initialized")

    def __load_config(self):

        self.__actions(self.conf.get('actions', dict()))

    def __process_packets(self, packets, out_writer, drop_writer, validation_file):
        """
        :type packets: list of [Packet]
        :return A tuple with the number of packets anonymized and the number of packets dropped
        :rtype (int, int)
        """

        nb_dropped = 0
        nb_anonymized = 0

        for index, packet in enumerate(packets):
            packet_id = index + 1  # packet id stark with 1

            try:
                try:
                    self.__process_packet(packet, validation_file)

                except Exception as e:
                    if isinstance(e, ExplicitDropException):
                        self.app.log.info("Packet explicitly dropped: id = '{}', {}, {}".format(packet_id, e.message,
                                                                                                packet.summary()))
                    elif isinstance(e, ImplicitDropException):
                        self.app.log.error("Packet implicitly dropped: id = '{}', {}, {}".format(packet_id, e.message,
                                                                                                 packet.summary()))
                    else:
                        raise

                    if self.app.phase is Phase.phase_3:
                        new_pkt = Packet(str(packet))
                        new_pkt.time = packet.time
                        drop_writer.write(new_pkt)
                    nb_dropped += 1

                else:
                    if self.app.phase is Phase.phase_3:
                        out_writer.write(packet)
                    nb_anonymized += 1

            except Exception as e:
                self.app.log.critical("Unexpected error: " + str(e) + str(packet))
        return nb_anonymized, nb_dropped

    def __process_packet(self, packet, validation_file):

        layer = packet
        while not isinstance(layer, NoPayload):

            layer_name = layer.__class__.__name__
            layer_action = self.layers[layer_name]

            if layer_action.default is _LayerActionEnum.explicit_pass:
                pass

            elif layer_action.default is _LayerActionEnum.explicit_drop:
                raise ExplicitDropException("layer = '{}'".format(layer_name))

            elif layer_action.default is _LayerActionEnum.implicit_drop:
                raise ImplicitDropException("layer = '{}'".format(layer_name))

            elif layer_action.default is _LayerActionEnum.implicit_pass:

                for field_name in layer.fields.iterkeys():
                    action = layer_action.fields[field_name]
                    try:
                        self.__process_field(layer, field_name, action, validation_file)
                    except ExplicitDropException as e:
                        raise ExplicitDropException("layer = '{}', {}".format(layer_name, e.message))
                    except ImplicitDropException as e:
                        raise ImplicitDropException("layer = '{}', {}".format(layer_name, e.message))
            else:
                raise ValueError("layer_action is invalid: default = '{}'".format(layer_action.default))

            layer = layer.payload  # Get next layer

    def __process_value(self, action, value, validation_file):

        v_type = type(value)

        if v_type is int:
            value = int(value)
        elif v_type is long:
            value = long(value)
        else:
            value = str(value)

        if self.app.phase is Phase.phase_1:
            action.discover(value)
        elif self.app.phase is Phase.phase_3:
            return action.anonymize(value)
        elif self.app.phase is Phase.phase_4:
            value = action.anonymize(value)
            if value is not None and value is not '':
                validation_file.write(str(value) + '\n')

        return None

    def __process_field(self, layer, field_name, action, validation_file):
        """
        :type layer: Packet
        """

        field_value = getattr(layer, field_name)

        try:
            if isinstance(field_value, list):
                for index, element in enumerate(field_value):
                    field_value[index] = self.__process_value(action, element, validation_file)
            else:
                field_value = self.__process_value(action, field_value, validation_file)

            if self.app.phase is Phase.phase_3:
                setattr(layer, field_name, field_value)

        except ExplicitDropException as e:
            raise ExplicitDropException("field = '{}', action = {}, {}".format(field_name, action.name, e.message))
        except Exception as e:
            raise ImplicitDropException("field = '{}', action = {}, {}".format(field_name, action.name, str(e)))

    def __process_file(self, name):

        self.app.log.info("file:pcap: Start anonymization: File = '{}'".format(name))

        in_path = os.path.join(self.app.project.input, name)
        packets = rdpcap(in_path)

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

        stat = _Stat(self.app, name)

        try:
            stat.packets_anonymized, stat.packets_dropped = self.__process_packets(packets,
                                                                                   out_writer,
                                                                                   drop_writer,
                                                                                   validation_file)
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

    def __process_files(self):

        for name in self.files:
            self.__process_file(name)

    def discover(self):
        self.__process_files()

    def anonymize(self):
        self.__process_files()

    def validate(self):
        self.__process_files()

    def is_compatible(self, name):
        typedesc = magic.from_file(os.path.join(self.app.project.input, name))
        return str(typedesc).startswith("tcpdump capture file")

    def __actions(self, yml):

        lm = self.app.manager.layer
        am = self.app.manager.action

        if not isinstance(yml, dict):
            self.app.log.error("file:pcap: Invalid format for 'action'")
            return

        for k, v in dict(yml).iteritems():

            try:
                lm.get_layer_class(k)

            except Exception as e:
                self.app.log.error(e.message + ": File, in 'actions'")

            else:
                if 'other-fields' in v:
                    self.layers[k].other_fields = am.get_action(v['other-fields'])

                if 'fields' in v:
                    self.__actions_fields(k, v['fields'])
                else:
                    if v == 'pass':
                        self.layers[k].default = _LayerActionEnum.explicit_pass
                    elif v == 'drop':
                        self.layers[k].default = _LayerActionEnum.explicit_drop
                    else:
                        self.app.log.error("file:pcap: Invalid layer action, action = '{}'".format(v))

    def __actions_fields(self, layer, yml):

        am = self.app.manager.action

        if isinstance(yml, dict):

            for field_name, action_name in dict(yml).iteritems():

                try:
                    if action_name is None:
                        action = am.get_action("pass")
                    else:
                        action = am.get_action(action_name)

                except Exception as e:
                    self.app.log.error("Action '{}' not found: {}".format(action_name, e))

                else:
                    self.layers[layer].add_action(field_name, action)

        else:
            self.app.log.error(
                "Invalid format for 'fields': Filetype in 'bind_actions''" + layer.__name__ + "'")


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