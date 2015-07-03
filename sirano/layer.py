# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>

from scapy.layers.all import *
from sirano.plugins.layers.sip import *
from sirano.plugins.layers.rtp_payload import *
from sirano.manager import Manager


class LayerManager(Manager):
    """Manage Scapy Layer classes"""

    name = 'layer'

    layer_classes = None
    """Imported Layer plugins, the key contain the name and the value contain the class"""

    def __init__(self, app):
        Manager.__init__(self, app)
        self.yml = self.app.conf.setdefault('layer', dict())

    def configure(self):
        self.app.log.debug("manager:layer: Configured")
        self.__bind_layers()

    def get_layer_class(self, layer_name):
        """
        Get the class with the specified name

        :param layer_name: The name that correspond to the attribute name of the Layer to get
        :type layer_name: str
        """

        self.app.log.debug("manager:layer: Get layer '%s'", layer_name)

        if layer_name in globals():
            return globals()[layer_name]

        else:
            logging.warning("Layer \"" + layer_name + "\" not found")
            return None

    def __bind_layers(self):
        """Call the Scapy bind_layers function with  all entry in the configuration"""

        yml_conf = self.yml.setdefault('bind-layers', list())

        for elt in yml_conf:
            if "lower" in elt and "upper" in elt:

                lower = self.get_layer_class(elt["lower"])
                upper = self.get_layer_class(elt["upper"])

                if lower is not None and upper is not None:

                    if "fields" in elt:
                        fields = elt["fields"]
                    else:
                        fields = None

                    bind_layers(lower, upper, fields)

                else:
                    self.app.log.error("Filetype \"" +self.app.project.config + "\", in 'bind_layers'")

            else:
                if "lower" not in elt:
                    self.app.log.error("Key 'lower' is missing: Filetype \"" + self.app.project.config
                                       + "\", in 'bind_layers")

                if "upper" not in elt:
                    self.app.log.error("Key 'upper' is missing: Filetype \"" + self.app.project.config
                                       + "\", in 'bind_layers")



