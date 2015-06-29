# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>


class SiranoException(Exception):
    """
    Root Exception for the Sirano application
    """

    def __init__(self, message=''):
        """
        Initialize the exception with a message

        :param message: The message
        :type message: str
        """
        self.message = message

    def __str__(self):
        return "sirano:" + self.message


class ScapyPacketException(SiranoException):
    """
    Exception for the file plugin
    """

    def __init__(self, message=''):
        super(ScapyPacketException, self).__init__(message)


class DropException(ScapyPacketException):
    """
    Exception when the entire element must be dropped
    """

    def __str__(self):
        return "sirano:file:drop: " + self.message


class ImplicitDropException(DropException):
    """
    Exception when the DropException is not explicitly requested by the user
    """

    def __str__(self):
        return "sirano:file:drop:implicit: " + self.message


class ExplicitDropException(DropException):
    """
    Exception when the DropException is explicitly requested by the user
    """

    def __str__(self):
        return "sirano:file:drop:explicit: " + self.message


class ActionException(SiranoException):
    """
    Exception for Action plugins
    """

    def __str__(self):
        return "sirano:action: message = '{}'".format(self.message)


class DataException(SiranoException):
    """
    Exception for Data plugins
    """

    def __init__(self, data, message=''):
        super(DataException, self).__init__(message)
        self.data = data

    def __str__(self):
        return "sirano:data: data='{}', message = '{}'".format(self.data.name, self.message)


class InvalidValueDataException(DataException):
    """
    Exception when a value is not valid for the data plugin
    """

    def __init__(self, data, value, message=''):
        """
        Constructor
        :param data: The data that have generated the exception
        :type data: sirano.data.Data
        :param value: The value that is invalid
        :type value: str
        """
        super(InvalidValueDataException, self).__init__(data, message)
        self.value = value

    def __str__(self):
        return "sirano:data: data = '{}', value = '{}', message = '{}'".format(self.data.name, self.value, self.message)


class UnsupportedFormatException(ActionException):
    """
    Exception when the format of a value is invalid
    """
    def __str__(self):
        return "sirano:action:Unsupported format: message = '{}'".format(
            self.message)


class PassException(ActionException):
    """
    Exception when the anonymize function must be skipped
    """
