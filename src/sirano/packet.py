from collections import defaultdict
from scapy.packet import Packet, NoPayload
from sirano.exception import ExplicitDropException, ImplicitDropException
from sirano.utils import AppBase


class PacketAnonymizer(AppBase):

    def __init__(self, app):
        """
        Constructor
        :param app: The application instance
        :type app: App
        """
        super(PacketAnonymizer, self).__init__(app)

        self.conf = app.conf.get('packet', dict)
        """The file configuration given by the YAML configuration file"""

        self.layers = self.__layers()

    def anonymize(self, packet):
        """
        Anonymize the specified packet
        :param packet: The scapy packet to anonymize
        :type packet: Packet
        """
        assert isinstance(packet, Packet)
        for layer in self.__packet_layers(packet):
            try:
                self.layers[layer.__class__.__name__].anonymize(layer)
            except Exception as e:
                raise type(e)("layer = '{}', {}".format(layer.__class__.__name__, e.message))

    def discover(self, packet):
        """
        Discover the sensitive data in the specified packet
        :param packet: The scapy packet
        :type packet: Packet
        """
        assert isinstance(packet, Packet)
        for layer in self.__packet_layers(packet):
            try:
                self.layers[layer.__class__.__name__].discover(layer)
            except Exception as e:
                raise type(e)("layer = '{}', {}".format(layer.__class__.__name__, e.message))

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
        validation = list()
        for layer in self.__packet_layers(packet):
            try:
                layer_validation = self.layers[layer.__class__.__name__].validate(layer)
                if layer_validation is not None:
                    validation.append(layer_validation)
            except Exception as e:
                raise type(e)("layer = '{}', {}".format(layer.__class__.__name__, e.message))

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
            layer = layer.payload # Get the next layer

    def __layers(self):
        """
        Creates the layers property from the configuration file
        :return: The layers dictionary with layer name and layer action
        :rtype dict[str, LayerAction]
        """
        layers = defaultdict(lambda: ImplicitDropLayerAction(self.app))
        for layer, conf in self.conf.get('layers', dict).iteritems():
            if isinstance(conf, str):
                if conf == 'pass':
                    layers[layer] = PassLayerAction(self.app)
                elif conf == 'drop':
                    layers[layer] = ExplicitDropLayerAction(self.app)
                else:
                    self.app.log.error("packet: Invalid action = '{}' for layer = '{}' in {}".format(conf, layer,
                                                                                             self.app.project.config))
            else:
                layers[layer] = AnonymizeLayerAction(self.app, conf)
        return  layers



class LayerAction(AppBase):
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

class AnonymizeLayerAction(LayerAction):

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
        for field in layer.fields.iterkeys():
            try:
                self.__discover_field(layer, field)
            except Exception as e:
                raise type(e)("field = '{}', {}".format(field, e.message))
        
    def anonymize(self, layer):
        for field in layer.fields.iterkeys():
            try:
                self.__anonymize_field(layer, field)
            except Exception as e:
                raise type(e)("field = '{}', {}".format(field, e.message))

    def validate(self, layer):
        validation = list()
        for field in layer.fields.iterkeys():
            try:
                validation.append(self.__validate_field(layer, field))
            except Exception as e:
                raise type(e)("field = '{}', {}".format(field, e.message))

        return '{}:\n  {}'.format(layer.__class__.__name__, '\n  '.join(validation))

    def __discover_field(self, layer, field):
        """
        Discover the field for from the specified layer
        :param layer: The scapy layer
        :type layer: Packet
        :param field: The field name
        :type field: str
        """
        action = self.fields[field]
        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    self.__discover_value(action, value)
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
        action = self.fields[field]

        if action.name == 'pass' and layer.__class__.__name__ == 'IP' and field == 'options':
            return

        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    values[index] = self.__anonymize_value(action, value)
            else:
                values = self.__anonymize_value(action, values)
            setattr(layer, field, values) # Update the field

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
        action = self.fields[field]
        values = getattr(layer, field)

        if values is not None:
            if isinstance(values, list):
                for index, value in enumerate(values):
                    values[index] = self.__anonymize_value(action, value)
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
        value = value_type(value) # Convert the object to its type
        try:
            action.discover(value)
        except Exception as e:
            raise type(e)("action = '{}', {}".format(action.name, e.message))

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
        value = value_type(value) # Convert the object to its type
        try:
            value = action.anonymize(value)
        except Exception as e:
            raise type(e)("action = '{}', {}".format(action.name, e.message))
        else:
            if value is not None:
                value = value_type(value) # Cast to the original type
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

        default_action =  am.get_action(self.conf.get('other-fields','implicit-drop'))
        fields = defaultdict(lambda: default_action)

        conf = self.conf.get('fields', dict())

        for field, action in conf.iteritems():
            fields[field] = am.get_action(action)

        return fields

class PassLayerAction(LayerAction):
    """
    Layer Action to pass a layer without anonymization
    """
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
    def discover(self, layer):
        raise ExplicitDropException()

    def anonymize(self, layer):
        raise ExplicitDropException()

    def validate(self, layer):
        raise ExplicitDropException()

class ImplicitDropLayerAction(LayerAction):
    """
    Layer Action to drop implicitly a layer

    This is the default layer action, that mean its is not configured by the user
    """
    def discover(self, layer):
        raise ImplicitDropException()

    def anonymize(self, layer):
        raise ImplicitDropException()

    def validate(self, layer):
        raise ImplicitDropException()