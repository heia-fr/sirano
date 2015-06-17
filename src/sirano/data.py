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
import os

import yaml

from sirano.manager import Manager


class _DataMetaclass(type):
    """Metaclass to create self-registering Data plugins"""

    def __init__(cls, name, bases, attributes):
        """Called when an Action plugin is imported"""

        super(_DataMetaclass, cls).__init__(name, bases, attributes)

        dc = DataManager.data_classes

        if isinstance(dc, dict):
            name = attributes['name']
            if name in dc:
                raise ImportError("Action class with property name = '%s' already exists")
            else:
                dc[name] = cls
        else:
            DataManager.data_classes = dict()


class DataManager(Manager):
    """
    Manage both classes and the instances of plugins Data
    """

    name = 'data'
    data_classes = None
    """Imported Data plugins, the key contain the name and the value contain the class"""

    def __init__(self, app):
        Manager.__init__(self, app)

        self.data = dict()

    def configure(self):
        dirpath = os.path.dirname(__file__) + '/plugins/data/'
        for f in os.listdir(dirpath):
            if f not in ['.', '..', '__init__.py'] and f.endswith('.py'):
                self.__create_data(f[:-3])

        self.app.log.debug("manager:data: Configured")

    def get_data(self, name):
        """
        Get the instance of the Data class which have the specified name

        :param name: the name of the Data class
        :type name: str
        """
        return self.data[name]

    def __create_data(self, name):
        """Create a Data object and import it if necessary

        :param name: The name of the app to create
        :type name: str
        """
        try:
            d_cls = self.data_classes[name]
        except KeyError:
            __import__('sirano.plugins.data.' + name)
            d_cls = self.data_classes[name]

        d = d_cls(self.app)
        self.data[name] = d

        return d

    def load_all(self):
        """Call load method for all Data instance"""
        for _, d in self.data.iteritems():
            d.load()

    def process_all(self):
        """Call process method for all Data instance"""
        for _, d in self.data.iteritems():
            d.process()

    def clear_all(self):
        """Call clear method for all Data instance"""
        for _, d in self.data.iteritems():
            d.clear()

    def save_all(self):
        """Call save method for all Data instance"""
        for _, d in self.data.iteritems():
            d.save()

    def guess_data(self, value):
        """
        Guess which Data class to use for the specified value

        :param value: The value
        :type value: str

        :return the Data class
        :rtype Data
        """

        l = dict()

        for n, d in self.data.iteritems():
            if d.is_valid(value):
                l[n] = d

        s = len(l)

        if s == 0:
            self.app.log.critical("data:manager:guess_data: data type unknown for '%s'", value)
        elif s > 1:
            k = l.viewkeys()
            self.app.log.critical(
                "data:manager:guess_data: Multiple ambiguous data type, %s are possible for value '%s'",
                k, value)
        else:
            _, d = l.popitem()
            return d

    def add_value(self, value):
        """
        Add a value to the correct Data class

        :param value: the value to add
        :type value: str
        """

        d = self.guess_data(value)

        d.add_value(value)

    def get_replacement(self, value):
        """
        Get a replacement value with the correct Data class

        :param value: The value to replace
        :type value: str

        :return The replacement value
        :rtype str
        """

        d = self.guess_data(value)
        return d.get_replacement(value)


class Data():
    """
    Superclass for all Data plugins
    """

    name = None
    """The name of the Data plugin (must be redefined in subclasses)"""

    __metaclass__ = _DataMetaclass

    def __init__(self, app):
        """
        :param app: The application instance
        :type app: App
        """

        self.app = app
        """The application instance"""

        self.path = os.path.join(self.app.project.data, self.name + '.yml')
        """The path of the YAML file that contain the data is stored"""

        self.conf = app.conf.get(self.name, dict)
        """The data configuration given by the YAML configuration file"""

        self.data = defaultdict(dict)

    def load(self):
        """Load data from the YAML file"""

        if not os.path.isfile(self.path):
            return

        with file(self.path) as f:  # Read only by default
            self.data = yaml.load(f)

        if self.data is None:
            self.data = defaultdict(dict)

        self.app.log.debug("data:{}: Data loaded: File \"{}\"".format(self.name, self.path))

    def save(self):
        """Save data to the YAML file"""

        with file(self.path, 'w') as f:
            yaml.dump(dict(self.data), f, default_flow_style=False)

        self.app.log.debug("data:{}: Data saved: File \"{}\"".format(self.name, self.path))

    def process(self):
        """
        Process data

        This method must be overridden. It generates replacement value for all data entry.
        """
        raise NotImplementedError

    def clear(self):
        """
        Process data

        This method must be overridden. It makes all replacement value empty.
        """
        raise NotImplementedError

    def add_value(self, value):
        """
        Add a value to the data

        This method must be overridden.

       :param value: The data to add
       :type value: str
        """
        raise NotImplementedError

    def get_replacement(self, value):
        """
        Get the replacement value for the given value

        This method must be overridden.

        :param value: The value to replace
        :type value: str

        :return The replacement value
        :rtype str
        """
        raise NotImplementedError

    def is_valid(self, value):
        """
        Check if the format of the given value is valid with this Data class

        This method must be overridden.

        :param value: The value
        :type value: str

        :return True when the format of value is valid, False otherwise
        :rtype boolean
        """
        raise NotImplementedError
