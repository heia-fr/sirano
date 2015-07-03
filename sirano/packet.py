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
from scapy.packet import Packet, NoPayload
from sirano.exception import ExplicitDropException, ImplicitDropException, DropException, ErrorDropException
from sirano.utils import AppBase, find_one_dict_by_key, raise_drop_exception


class PacketAnonymizer(AppBase):

    def __init__(self, app):
        """
        Constructor
        :param app: The application instance
        :type app: App
        """
        super(PacketAnonymizer, self).__init__(app)

        self.conf = app.conf.setdefault('packet', dict())
        """The file configuration given by the YAML configuration file"""

        self.report = app.report.setdefault('packet', dict())
        """
        The report for the JSON file
        :type: dict[str, object]
        """

        self.layers = self.__layers()

        self.reset()

        self.current_packet = None
        """
        The packet currently processed or None
        :type: Packet
        """

    def anonymize(self, packet):
        """
        Anonymize the specified packet
        :param packet: The scapy packet to anonymize
        :type packet: Packet
        """
        assert isinstance(packet, Packet)
        self.current_packet = packet
        for layer in self.__packet_layers(packet):
            try:
                name = layer.__class__.__name__
                layer_action = self.layers[name]
                layer_action.anonymize(layer)
            except Exception as e:
                if isinstance(e, ExplicitDropException):
                    self.__report_increment_layer(name, 'explicit_drop')
                    self.__report_increment_packet(packet, 'explicit_drop')
                elif isinstance(e, ImplicitDropException):
                    self.__report_increment_layer(name, 'implicit_drop')
                    self.__report_increment_packet(packet, 'implicit_drop')
                else:
                    self.__report_increment_layer(name, 'error')
                    self.__report_increment_packet(packet, 'error')
                raise_drop_exception(e, "layer = '{}'".format(name))
            else:
                if layer_action.name == 'anonymize':
                    self.__report_increment_layer(name, 'anonymized')
                elif layer_action.name == 'pass':
                    self.__report_increment_layer(name, 'pass')
        self.__report_increment_packet(packet, 'anonymized')
        self.current_packet = None

    def discover(self, packet):
        """
        Discover the sensitive data in the specified packet
        :param packet: The scapy packet
        :type packet: Packet
        """
        assert isinstance(packet, Packet)
        self.current_packet = packet
        for layer in self.__packet_layers(packet):
            try:
                name = layer.__class__.__name__
                layer_action = self.layers[name]
                layer_action.discover(layer)
            except Exception as e:
                if isinstance(e, ExplicitDropException):
                    self.__report_increment_layer(name, 'explicit_drop', True)
                    self.__report_increment_packet(packet, 'explicit_drop', True)
                elif isinstance(e, ImplicitDropException):
                    self.__report_increment_layer(name, 'implicit_drop', True)
                    self.__report_increment_packet(packet, 'implicit_drop', True)
                else:
                    self.__report_increment_layer(name, 'error', True)
                    self.__report_increment_packet(packet, 'error', True)
                raise_drop_exception(e, "layer = '{}'".format(name))
            else:
                if layer_action.name == 'anonymize':
                    self.__report_increment_layer(name, 'anonymized', True)
                elif layer_action.name == 'pass':
                    self.__report_increment_layer(name, 'pass', True)
        self.__report_increment_packet(packet, 'anonymized', True)
        self.current_packet = Packet

    def validate(self, packet):
        """
        Validate the sensitive data in the specified packet.

        The sensitive date will be replaced with a empty string.
        :param packet: The scapy packet
        :type packet: Packet
        :return: The packet under text format
        :rtype str
        """
        assert isinstance(packet, Packet)
        self.current_packet = packet
        validation = list()
        for layer in self.__packet_layers(packet):
            try:
                name = layer.__class__.__name__
                layer_validation = self.layers[name].validate(layer)
                if layer_validation is not None:
                    validation.append(layer_validation)
            except Exception as e:
                raise_drop_exception(e, "layer = '{}'".format(name))
        self.current_packet = None
        return '\n\n'.join(validation)

    @staticmethod
    def __packet_layers(packet):
        """
        Generator that return all layers in the specified packet
        :param packet: The scapy packet
        :type packet: Packet
        :return: The layer generator
        :rtype list[Packet]
        """
        layer = packet
        while not isinstance(layer, NoPayload):
            yield layer
            layer = layer.payload  # Get the next layer

    def __layers(self):
        """
        Creates the layers property from the configuration file
        :return: The layers dictionary with layer name and layer action
        :rtype dict[str, LayerAction]
        """
        layers = defaultdict(lambda: ImplicitDropLayerAction(self.app))
        for layer, conf in self.conf.setdefault('layers', dict()).items():
            if isinstance(conf, str):
                if conf == 'pass':
                    layers[layer] = PassLayerAction(self.app)
                elif conf == 'drop':
                    layers[layer] = ExplicitDropLayerAction(self.app)
                else:
                    self.app.log.error("packet: Invalid action = '{}' for layer = '{}' in {}".format(
                        conf, layer, self.app.project.config))
            else:
                layers[layer] = AnonymizeLayerAction(self.app, conf)
        return layers

    def __report_increment_layer(self, name, a_property, discover=False):
        """
        Increment a layer entry in the report
        :param name: The name of the layer
        :type name: str
        :param a_property: The property to increment
        :type a_property: str
        :param discover: True for the discovery phase
        :type discover: False | True
        """
        if discover:
            report = [self.report.setdefault('discovery', dict()).setdefault('layers', list())]
        else:
            report = [self.report.setdefault('anonymization', dict()).setdefault('layers', list()),
                      self.report.setdefault('files', dict()).setdefault(self.app.manager.file.current_file,
                                                                         dict()).setdefault('layers', list())]

        """:type: list[listt[dict]]"""

        for layers in report:
            entry = find_one_dict_by_key(layers, 'name', name)
            if entry is None:
                entry = {'name': name,
                         'pass': 0,
                         'implicit_drop': 0,
                         'explicit_drop': 0,
                         'anonymized': 0,
                         'error': 0}
                layers.append(entry)

            entry[a_property] += 1

    def __report_increment_packet(self, packet, a_property, discover=False):
        """
        Increment a layer entry in the report
        :param packet: The packet
        :type packet: Packet
        :param a_property: The property to increment
        :type a_property: str
        :param discover: True for the discovery phase
        :type discover: False | True
        """
        if discover:
            report = [self.report.setdefault('discovery', dict()).setdefault('packets', list())]
        else:
            report = [self.report.setdefault('anonymization', dict()).setdefault('packets', list()),
                      self.report.setdefault('files', dict()).setdefault(self.app.manager.file.current_file,
                                                                         dict()).setdefault('packets', list())]
        """:type: list[listt[dict]]"""

        name = self.__get_packet_layers(packet)
        for layers in report:
            entry = find_one_dict_by_key(layers, 'name', name)
            if entry is None:
                entry = {'name': name,
                         'pass': 0,
                         'implicit_drop': 0,
                         'explicit_drop': 0,
                         'anonymized': 0,
                         'error': 0}
                layers.append(entry)
            entry[a_property] += 1

    def reset(self):
        """
        Reset between phase
        """
        self.__report_reset()

    def __report_reset(self):
        """
        Reset the report
        """
        if self.app.phase == 1:
            a_global = self.report.setdefault('discovery', dict())
        elif self.app.phase == 3:
            a_global = self.report.setdefault('anonymization', dict())
            files = self.report.setdefault('files', dict())
            for a_file in files.values():
                a_file['packets'] = list()
                a_file['layers'] = list()
        elif self.app.phase == 4:
            a_global = self.report.setdefault('validation', dict())
        else:
            a_global = dict()
        """:type: dict[str, object]"""
        a_global['packets'] = list()
        a_global['layers'] = list()


    def __get_packet_layers(self, packet):
        """
        Get packet layers to readable format
        :param packet: The packet
        :type packet: Packet
        :return A string with the packet name
        :rtype: str
        """
        names = list()
        for layer in self.__packet_layers(packet):
            names.append(layer.__class__.__name__)

        return ' / '.join(names)


class LayerAction(AppBase):
    name = None
    """
    The name of the layer action
    :type: str
    """

    def __init__(self, app):
        super(LayerAction, self).__init__(app)

    def discover(self, layer):
        """
        Discover the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        """
        raise NotImplementedError

    def anonymize(self, layer):
        """
        Anonymize the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        """
        raise NotImplementedError

    def validate(self, layer):
        """
        Validate the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        """
        raise NotImplementedError


class DropExecption(object):
    pass


class AnonymizeLayerAction(LayerAction):
    name = "anonymize"

    def __init__(self, app, conf):
        """
        :param app: The application instance
        :type app: App
        :param conf: The configuration for the layer
        :type conf: dict
        """
        super(AnonymizeLayerAction, self).__init__(app)
        self.conf = conf
        """
        The configuration for the layer
        :type : dict
        """
        self.fields = self.__fields()

    def discover(self, layer):
        for field in layer.fields.keys():
            try:
                self.__discover_field(layer, field)
            except Exception as e:
                raise_drop_exception(e, "field = '{}'".format(field))

    def anonymize(self, layer):
        for field in layer.fields.keys():
            try:
                self.__anonymize_field(layer, field)
            except Exception as e:
                raise_drop_exception(e, "field = '{}'".format(field))

    def validate(self, layer):
        validation = list()
        for field in layer.fields.keys():
            try:
                validation.append(self.__validate_field(layer, field))
            except Exception as e:
                raise_drop_exception(e, "field = '{}'".format(field))

        return '{}:\n  {}'.format(layer.__class__.__name__, '\n  '.join(validation))

    def __discover_field(self, layer, field):
        """
        Discover the field for from the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        :param field: The field name
        :type field: str
        """
        action = self.fields[field.lower()]
        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    if isinstance(values, Packet):
                        self.app.packet.discover(value)
                    else:
                        self.__discover_value(action, value)
            else:
                if isinstance(values, Packet):
                    self.app.packet.discover(values)
                else:
                    self.__discover_value(action, values)

    def __anonymize_field(self, layer, field):
        """
        Anonymize the field for from the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        :param field: The field name
        :type field: str
        """
        action = self.fields[field.lower()]

        # if action.name == 'pass' and layer.__class__.__name__ == 'IP' and field == 'options':
        #     return

        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    if isinstance(value, Packet):
                        self.app.packet.anonymize(value)
                    else:
                        values[index] = self.__anonymize_value(action, value)
            else:
                if isinstance(values, Packet):
                    self.app.packet.anonymize(values)
                else:
                    values = self.__anonymize_value(action, values)
            setattr(layer, field, values)  # Update the field

    def __validate_field(self, layer, field):
        """
        Validate the field for from the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        :param field: The field name
        :type field: str
        :return The value for the validation
        :rtype str
        """
        action = self.fields[field.lower()]
        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    if isinstance(value, Packet):
                        values[index] = self.app.packet.validate(value)
                    else:
                        values[index] = self.__anonymize_value(action, value)
            else:
                if isinstance(values, Packet):
                    values = self.app.packet.validate(values)
                else:
                    values = self.__anonymize_value(action, values)
        return '{}: {}'.format(field, values)

    @staticmethod
    def __discover_value(action, value):
        """
        Discover the value with the specified action
        :param action: The action
        :type action: Action
        :param value: The value
        :type value: object
        """
        value_type = type(value)
        value = value_type(value)  # Convert the object to its type
        try:
            action.discover(value)
        except Exception as e:
            raise_drop_exception(e, "action = '{}', value = {}".format(action.name, repr(value)))

    @staticmethod
    def __anonymize_value(action, value):
        """
        Anonymize the value with the specified action
        :param action: The action
        :type action: Action
        :param value: The value
        :type value: object
        :return The anonymized value
        :rtype int | long | str
        """
        value_type = type(value)
        value = value_type(value)  # Convert the object to its type
        try:
            value = action.anonymize(value)
        except Exception as e:
            raise_drop_exception(e, "action = '{}', value = {}".format(action.name, repr(value)))
        else:
            if value is not None:
                value = value_type(value)  # Cast to the original type
            return value

    def __fields(self):
        """
        Get the dictionnary with an action for each field
        :return The fields action dictionnary
        :rtype dict[str, Action]
        """
        am = self.app.manager.action

        if not isinstance(self.conf, dict):
            self.app.log.error("file:pcap: Invalid format for 'action'")
            return

        default_action = am.get_action(self.conf.setdefault('other-fields', 'implicit-drop'))
        fields = defaultdict(lambda: default_action)

        conf = self.conf.setdefault('fields', dict())

        for field, action in conf.items():
            fields[field.lower()] = am.get_action(action)

        return fields


class PassLayerAction(LayerAction):
    """
    Layer Action to pass a layer without anonymization
    """

    name = "pass"

    def discover(self, layer):
        pass

    def anonymize(self, layer):
        pass

    def validate(self, layer):
        pass


class ExplicitDropLayerAction(LayerAction):
    """
    Layer Action to drop explicitly a layer
    """

    name = "explicit-drop"

    def discover(self, layer):
        raise ExplicitDropException('layer configured to be drop')

    def anonymize(self, layer):
        raise ExplicitDropException('layer configured to be drop')

    def validate(self, layer):
        raise ExplicitDropException('layer configured to be drop')


class ImplicitDropLayerAction(LayerAction):
    """
    Layer Action to drop implicitly a layer

    This is the default layer action, that mean its is not configured by the user
    """

    name = "implicit-drop"

    def discover(self, layer):
        raise ImplicitDropException('layer not configured')

    def anonymize(self, layer):
        raise ImplicitDropException('layer not configured')

    def validate(self, layer):
        raise ImplicitDropException('layer not configured')
