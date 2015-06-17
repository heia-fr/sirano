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
    """
    Contain the File plugin name with its class
    :type : list[__FiletypeMetaclass]
    """

    def __init__(self, app):
        Manager.__init__(self, app)

        self.files = list()
        """
        File object to anonymize
        :type : list[File]
        """

        self.priority = dict()
        """
        The priority of the File for the processing order
        :type dict[str, File]
        """

    def configure(self):
        if isinstance(self.conf, dict):
            for name, data in self.conf.iteritems():
                if 'priority' in data:
                    self.__import_file(name, data['priority'])
                else:
                    # TODO Config exception
                    Exception("Key priority not found")
        else:
            # TODO Config exception
            Exception("Filetype format invalid")

        self.app.log.debug("manager:files: Configured")

    def __import_file(self, name, priority):
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

        f_cls.priority = priority

    def __get_file_cls(self, path):
        """Find a File plugin for a specified file

        :param filename: The path of the file
        :type filename: str
        """
        for f_cls in self.file_classes.itervalues():
            if f_cls.is_compatible(path):
                return f_cls

        self.app.log.critical("manager:file: File type not detected for \"%s\"", path)
        return None

    def add_files(self):
        """Adds all files that are in the input file"""

        for root, dirs, files in os.walk(self.app.project.input):
            for name in files:

                if name.startswith('.'):
                    continue

                path = os.path.join(root, name)

                # Relative path of the file from the input directory
                r_path = os.path.relpath(path, self.app.project.input)

                f_cls = self.__get_file_cls(path)

                if f_cls is not None:
                    f = f_cls(self.app, r_path)
                    self.files.append(f)

        self.files.sort(key=lambda f: f.priority)

    def anonymize_all(self):
        """Launch the anonymize method for all files"""
        for f in self.files:
            f.anonymize()

    def discover_all(self):
        """Launch the discover method for all files"""
        for f in self.files:
            f.discover()

    def validate_all(self):
        """Launch the validate method for all files"""
        for f in self.files:
            f.validate()


class File:
    """Superclass for all actions"""

    name = None
    """
    The name of the action, this class attribute must be declared in subclasses
    :type : str
    """

    priority = None
    """
    The priority is the order for the file processing
    :type : int
    """

    __metaclass__ = _FiletypeMetaclass

    def __init__(self, app, file):
        """
        Constructor
        :param app: The apélication instance
        :rtype App
        :param file: The relative path of the file from the in directory
        :type file: str
        """
        self.app = app
        """
        The instance of the application
        :type : App
        """

        self.file = file
        """
        The relative path of the file from the in directory
        :type : str
        """

        self.conf = app.conf.get('file', dict).get(self.name, dict())
        """
        The file configuration given by the YAML configuration file
        :type : dict[str, dict]
        """

    @classmethod
    def is_compatible(cls, filename):
        """
        Check if a file is compatible with the File class

        This class method must be overridden.

        :param filename: The file name of the file to test
        :type filename: str

        :return True when the file is compatible, False otherwise
        """
        raise NotImplementedError

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
