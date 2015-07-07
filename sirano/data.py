# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>

from collections import defaultdict
import os
import re
import datetime

import yaml

from sirano.exception import DataException, InvalidValueDataException

from sirano.manager import Manager
from sirano.utils import date_to_json, AppBase


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
        self.__report_data_reset()
        self.app.log.debug("manager:data: Configured")

    def get_data(self, name):
        """
        Get the instance of the Data class which have the specified name

        :param name: the name of the Data class
        :type name: str
        :return The data plugin
        :rtype Data
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
        for _, d in self.data.items():
            d.load()

    def process_all(self):
        """Call process method for all Data instance"""
        start = datetime.datetime.now()
        for _, d in self.data.items():
            d.process()
        end = datetime.datetime.now()
        self.app.report_update_phase('Generate', {'start': date_to_json(start),
                                     'end': date_to_json(end),
                                     'duration': date_to_json(end - start)})

    def save_all(self):
        """Call save method for all Data instance"""
        for d in self.data.values():
            d.save()

    def find_values_all(self, string):
        """
        Call find_values method for all Data instance
        :param string: The string where search
        :type string: str
        :return: Dictionnary with data name and values
        :rtype: dict[str, list[str]]
        """
        values = dict()
        for name, data in self.data.items():
            values[name] = data.find_values(string)
        return  values

    def set_clean_mode_all(self, mode):
        """
        Set the clean mode for all data
        :param mode: True if the clean mode is activated, False otherwise
        :type mode: True | False
        """
        for name, data in self.data.items():
            data.clean_mode = mode

    def guess_data(self, value):
        """
        Guess which Data class to use for the specified value

        :param value: The value
        :type value: str

        :return the Data class
        :rtype Data
        """

        l = dict()


        for n, d in self.data.items():
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
        :raise
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

    def report_data_increment(self, data, a_property):
        data_list = self.report.setdefault('data', list())
        """:type: list[dict]"""
        entry = None
        for d in data_list:
            if d['name'] == data.name:
                entry = d
        if entry is None:
            entry = {'name': data.name,
                     'invalid': 0,
                     'error': 0,
                     'discovered': 0,
                     'added': 0}
            data_list.append(entry)
        entry[a_property] += 1

    def report_stats(self, data):
        stats = self.report.setdefault('stats', list())
        """:type: list[dict]"""

        entry = None
        for stat in stats:
            if stat['name'] == data.name:
                entry = stat

        if entry is None:
            entry = {'name': data.name}
            stats.append(entry)

        entry['number'] = data.get_number_of_values()

    def __report_data_reset(self):
        """
        Reset the report data
        """
        for d in self.report.setdefault('data', list()):
            d['invalid'] = 0
            d['error'] = 0
            d['discovered'] = 0
            # Added is not reset for preserving the counter from the first discovery


class Data(AppBase):
    """
    Superclass for all Data plugins
    """

    name = None
    """The name of the Data plugin (must be redefined in subclasses)"""

    __metaclass__ = _DataMetaclass

    def __init__(self, app):
        super(Data, self).__init__(app)

        self.app.log.debug('data:{}:__init__()'.format(self.name))

        self.path = os.path.join(self.app.project.data, self.name + '.yml')
        """The path of the YAML file that contain the data is stored"""

        self.conf = app.conf.setdefault('data', dict()).setdefault(self.name, dict())
        """
        The data configuration given by the YAML configuration file
        :type: dict[str, object]
        """

        self.data = None
        """Data from the YAML file"""

        self.manager = self.app.manager.data
        """
        Data manager
        :type: DataManager
        """

        self.report = app.report.setdefault('plugins', dict()).setdefault('data', dict()).setdefault(self.name, dict())
        """
        Report data for the JSON file
        :type: dict[str, object]
        """

        self.clean_mode = False
        """
        Clean mode, if True all replacement value will be an empty string
        :type: True | False
        """

        self.__exclusion = list()
        """
        List of regular expression to exclude in find_values()
        :type: list
        """

    def load(self):
        """Load data from the YAML file"""
        self.app.log.debug("data:{}:load()".format(self.name))
        self.__data_report_reset()

        if os.path.isfile(self.path):
            with file(self.path) as f:  # Read only by default
                self.data = yaml.load(f)

        if self.data is None:
            self.data = defaultdict(dict)

        self.app.log.debug("data:{}: Data loaded: File \"{}\"".format(self.name, self.path))

        exclusions = self.app.conf.get('data', dict()).get('global', dict()).get('find-exclusion', list())
        if exclusions:
            for exclusion in exclusions:
                self.__exclusion.append(re.compile(exclusion, re.IGNORECASE))

        self.post_load()

    def post_load(self):
        """
        Method called after loading data

        Can be overridden
        """
        self.app.log.debug('data:{}:post_load()'.format(self.name))
        pass

    def pre_save(self):
        """
        Method called before saving data

        Can be overridden
        """
        self.app.log.debug('data:{}:pre_save()'.format(self.name))
        pass

    def save(self):
        """Save data to the YAML file"""

        self.manager.report_stats(self)

        self.pre_save()

        self.app.log.debug('data:{}:save()'.format(self.name))

        with open(self.path, 'w') as f:
            yaml.dump(dict(self.data), f, default_flow_style=False)

        self.app.log.debug("data:{}: Data saved: File \"{}\"".format(self.name, self.path))

    def process(self):
        """
        Process data

        This method must be overridden. It generates replacement value for all data entry.
        """
        raise NotImplementedError

    def add_value(self, value, validate=True):
        """
        Add a value to the data
        :param value: The value to add
        :type value: str
        :param validate: Validate the value (True by default)
        :type validate: True | False
        :return True if the value is added | False otherwise
        :raise DataException: The value is not valid
        """
        if value == '' or value is None:
            return
        if (not validate) or self.is_valid(value):
            try:
                added = self._add_value(value)
                if added:
                    self.manager.report_data_increment(self, 'added')
                self.manager.report_data_increment(self, 'discovered')
                return added
            except Exception:
                self.manager.report_data_increment(self, 'error')
                raise
        else:
            self.manager.report_data_increment(self, 'invalid')
            raise InvalidValueDataException("data = '{}', value = '{}'".format(self.name, value))

    def _add_value(self, value):
        """
        Method called by add_value()
        :param value: The value to add
        :type value: str
        :return True if
        :raise DataException: The value is not valid
        """
        raise NotImplementedError

    def get_replacement(self, value):
        """
        Get the replacement value for the given value
        :param value: The value to replace
        :type value: str
        :return The replacement value
        :rtype str
        """
        if self.clean_mode:
            return ''
        else:
            return self._get_replacement(value)

    def _get_replacement(self, value):
        """
        Method called by get_replacement()
        :param value: The value to replace
        :type value: str
        :return The replacement value
        :rtype str
        """
        raise NotImplementedError

    def has_value(self, value):
        """
        Check if the value exist
        :param value: The value
        :type value: str
        :return: True if exists, False otherwise
        :rtype: True | False
        """
        raise  NotImplementedError

    def has_replacement(self, replacement):
        """
        Check if a replacement value exist
        :param replacement: The replacement to check
        :type replacement: str
        :return: True if a replacement value exists, else False
        :rtype True | False
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

    def link_data(self, name, default):
        """
        Link YAML data to an object
        :param name: The name of the data
        :type name: str
        :param default: The default object if not exist
        :type default: type
        :return: The object reference
        """
        # Set default value if not exist or None
        if (not self.data.has_key(name)) or (self.data[name] is None):
            self.data[name] = default()
        return self.data[name]

    def get_number_of_values(self):
        """
        Get the number of values

        This method must be overridden.

        :return: The number of values
        :rtype: int
        """
        raise NotImplementedError

    def find_values(self, string):
        """
        Find values present in the string
        :param string: The string
        :return: The list of values
        :rtype: list[str]
        """
        string = string.replace('\n', ' ').replace('\r', ' ') # Remove new line

        for re_exclusion in self.__exclusion:
            for exclusion in re_exclusion.findall(string):
                string = string.replace(exclusion, '')

        return self._find_values(string)

    def _find_values(self, string):
        """
        Method called by find_values
        :param string: The string
        :return: The list of values
        :rtype: list[str]
        """
        raise NotImplementedError

    def data_report_processed(self, name, event):
        """
        Method called when a data is processed
        :param name: The name of the data type
        :type name: str
        :param event: The event name
        :type event: str
        """
        data = self.report.setdefault('processing', list())

        entry = None
        for d in data:
            if d.get('name') == name:
                entry = d
        if entry is None:
            entry = {'name': name,
                     'processed': 0,
                     'error': 0,
                     'number': 0}
            data.append(entry)

        entry[event] += 1

    def data_report_value(self, a_type, value, replacement):
        """
        Method called before saving database
        :param a_type: The type name
        :type a_type: str
        :param value: The value
        :type value: str
        :param replacement: The replacement value
        :type replacement: str
        """
        data = self.report.setdefault('values', dict()).setdefault(a_type, list())
        data.append({'value': value, 'replacement': replacement})

    def __data_report_reset(self):
        if self.app.phase == 2:
            # Processing
            data = self.report.setdefault('processing', list())
            for d in data:
                d['number'] = 0
                d['error'] = 0
                # processed should not be reseated

            # Values
            self.report['values'] = dict()