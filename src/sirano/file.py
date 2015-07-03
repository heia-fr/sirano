# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>

from heapq import heappush
from operator import attrgetter
import os
import datetime

from sirano.manager import Manager
from sirano.utils import date_to_json


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

        self.current_file = None
        """
        Current file processed
        :type: str
        """

    def configure(self):
        if isinstance(self.conf, dict):
            for name, data in self.conf.items():
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
                    self.__report_update_file(name, {'type': f.name,
                                                     'size' : f.size})

        if len(self.files) == 0:
            self.app.log.info("There are no files to process")

        self.files.sort(key=lambda x: x.priority)

    def anonymize_all(self):
        """Launch the anonymize method for all files"""
        start = datetime.datetime.now()
        for f in self.files:
            self.current_file = f.file
            f_start = datetime.datetime.now()
            f.anonymize()
            f_end = datetime.datetime.now()
            self.__report_update_file(f.file, {'anonymize_duration': date_to_json(f_end - f_start)})

        end = datetime.datetime.now()
        self.app.report_update_phase('Anonymize', {'start': date_to_json(start),
                                                 'end': date_to_json(end),
                                                 'duration': date_to_json(end - start)})

    def discover_all(self):
        """Launch the discover method for all files"""
        start = datetime.datetime.now()
        for f in self.files:
            self.current_file = f.file
            f_start = datetime.datetime.now()
            f.discover()
            f_end = datetime.datetime.now()
            self.__report_update_file(f.file, {'discover_duration': date_to_json(f_end - f_start)})

        end = datetime.datetime.now()
        self.app.report_update_phase('Discover', {'start': date_to_json(start),
                                                'end': date_to_json(end),
                                                'duration': date_to_json(end - start)})

    def validate_all(self):
        """Launch the validate method for all files"""
        start = datetime.datetime.now()
        for f in self.files:
            self.current_file = f.file
            f_start = datetime.datetime.now()
            f.validate()
            f_end = datetime.datetime.now()
            self.__report_update_file(f.file, {'validate_duration': date_to_json(f_end - f_start)})


        end = datetime.datetime.now()
        self.app.report_update_phase('Validate', {'start': date_to_json(start),
                                                'end': date_to_json(end),
                                                'duration': date_to_json(end - start)})

    def __report_update_file(self, name, values):
        """
        Update a file entry in the report
        :param name: The name of the file
        :type name: str
        :param values: The values to update
        :type values: dict
        """
        files = self.report.setdefault('files', list())
        """:type: list[dict]"""
        entry = None
        for f in files:
            if f['name'] == name:
                entry = f
        if entry is None:
            entry = {'name': name}
            files.append(entry)
        entry.update(values)

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

    def __init__(self, app, a_file):
        """
        Constructor
        :param app: The apélication instance
        :rtype App
        :param a_file: The relative path of the file from the in directory
        :type a_file: str
        """
        self.app = app
        """
        The instance of the application
        :type : App
        """

        self.file = a_file
        """
        The relative path of the file from the in directory
        :type : str
        """

        self.conf = app.conf.setdefault('file', dict()).setdefault(self.name, dict())
        """
        The file configuration given by the YAML configuration file
        :type : dict[str, dict]
        """

        self.size = self.__get_size()

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

    def __get_size(self):
        """
        Get the size of the file
        :return: The size human readable
        :rtype: str
        """
        statinfo = os.stat(os.path.join(self.app.project.input, self.file))
        nbytes = statinfo.st_size

        suffixes = ['B', 'KB', 'MB', 'GB', 'TB', 'PB']
        if nbytes == 0: return '0 B'
        i = 0
        while nbytes >= 1024 and i < len(suffixes)-1:
            nbytes /= 1024.
            i += 1
        f = ('%.2f' % nbytes).rstrip('0').rstrip('.')
        return '%s %s' % (f, suffixes[i])
