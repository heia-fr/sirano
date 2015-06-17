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

from heapq import heappush
import os

from sirano.manager import Manager


class _FiletypeMetaclass(type):
    """
    Metaclass to create self-registering Action plugins
    """

    def __init__(cls, name, bases, attributes):
        """
        Called when an Action plugin is imported
        """

        super(_FiletypeMetaclass, cls).__init__(name, bases, attributes)

        fm = FileManager.file_classes

        if isinstance(fm, dict):
            name = attributes['name']
            if name in fm:
                raise ImportError("Filetype class with property name = '%s' already exists")
            else:
                fm[name] = cls
        else:
            FileManager.file_classes = dict()


class FileManager(Manager):
    """
    Manager for each file format"
    """

    name = 'file'

    file_classes = None
    """Contain the File plugin name with its class"""

    def __init__(self, app):
        Manager.__init__(self, app)

        self.files = list()

    def configure(self):

        self.__load_config()
        self.app.log.debug("manager:files: Configured")

    def __load_config(self):
        """Load the configuration to its internal representation"""

        if isinstance(self.conf, dict):
            for name, data in self.conf.iteritems():
                if 'priority' in data:
                    self.__add_file(name, data['priority'])
                else:
                    # TODO Config exception
                    Exception("Key priority not found")
        else:
            # TODO Config exception
            Exception("Filetype format invalid")

    def __add_file(self, name, priority):
        """
        Add a File plugin with its priority

        :param name (str): The name of the plugin
        :type name: str
        :param priority: The priority of the File plugin (0 tis the highest priority)
        :type priority: int
        """

        try:
            f_cls = self.file_classes[name]
        except KeyError:
            __import__('sirano.plugins.files.' + name)
            f_cls = self.file_classes[name]

        f = f_cls(self.app)

        f_tuple = (priority, f)
        heappush(self.files, f_tuple)

    def __find_file(self, filename):
        """Find a File plugin for a specified file

        :param filename: The path of the file
        :type filename: str
        """

        for _, f in self.files:
            if f.is_compatible(filename):
                return f

        self.app.log.critical("manager:file: File type not detected for \"%s\"", filename)

    def add_files(self):
        """Adds all files that are in the input file"""

        for f in os.listdir(self.app.project.input):

            if f.startswith("."):
                continue

            ft = self.__find_file(f)

            ft.add_file(f)

    def anonymize_all(self):
        """Launch the anonymize method for all files"""

        for _, ft in self.files:
            ft.anonymize()

    def discover_all(self):
        """Launch the discover method for all files"""
        for _, ft in self.files:
            ft.discover()

    def validate_all(self):
        """Launch the validate method for all files"""
        for _, ft in self.files:
            ft.validate()


class File:
    """Superclass for all actions"""

    name = None
    """The name of the action, this class attribute must be declared in subclasses"""

    __metaclass__ = _FiletypeMetaclass

    def __init__(self, app):
        self.files = list()
        self.app = app
        """The instance of the application"""

        self.conf = app.conf.get('file', dict()).get(self.name, dict())
        """The file configuration given by the YAML configuration file"""

    def is_compatible(self, filename):
        """
        Check if a file is compatible with the File class

        This method must be overridden.

        :param filename: The file name of the file to test
        :type filename: str

        :return True when the file is compatible, False otherwise
        """
        raise NotImplementedError

    def add_file(self, filename):
        """
        Add a file to the list

        :param filename: The path of the file to add
        :type filename: str
        """
        self.files.append(filename)

    def anonymize(self):
        """
        Anonymize all files

        This method must be overridden
        """
        raise NotImplementedError

    def discover(self):
        """
        Discovering all files

        This method must be overridden
        """
        raise NotImplementedError

    def validate(self):
        """
        Validates all files

        This method must be overridden
        """
        raise NotImplementedError
