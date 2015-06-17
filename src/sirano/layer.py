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

from scapy.layers.all import *

from sirano.plugins.layers.sip import *
from sirano.manager import Manager


class LayerManager(Manager):
    """Manage Scapy Layer classes"""

    name = 'layer'

    layer_classes = None
    """Imported Layer plugins, the key contain the name and the value contain the class"""

    def __init__(self, app):
        Manager.__init__(self, app)
        self.yml = self.app.conf.get('layer', dict())

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

        yml_conf = self.yml.get('bind-layers', list())

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
                    self.app.log.error("Filetype \"" + self.app.config_file + "\", in 'bind_layers'")

            else:
                if "lower" not in elt:
                    self.app.log.error("Key 'lower' is missing: Filetype \"" + self.app.config_file
                                       + "\", in 'bind_layers")

                if "upper" not in elt:
                    self.app.log.error("Key 'upper' is missing: Filetype \"" + self.app.config_file
                                       + "\", in 'bind_layers")



