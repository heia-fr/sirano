# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>


class SiranoException(Exception):
    """
    Root Exception for the Sirano application
    """
    pass


class DropException(SiranoException):
    """
    Exception when the entire element must be dropped
    """
    pass


class ImplicitDropException(DropException):
    """
    Exception when the DropException is not explicitly requested by the user
    """
    pass


class ExplicitDropException(DropException):
    """
    Exception when the DropException is explicitly requested by the user
    """
    pass


class ErrorDropException(DropException):
    """
    Exception when an other exception cause a DropException
    """
    pass


class ActionException(SiranoException):
    """
    Exception for Action plugins
    """
    pass


class DataException(SiranoException):
    """
    Exception for Data plugins
    """
    pass


class InvalidValueDataException(DataException):
    """
    Exception when a value is not valid for the data plugin
    """
    pass


class ValueNotFoundException(DataException):
    """
    Exception when a value is not found in a data plugin
    """
    pass


class UnsupportedFormatException(ActionException):
    """
    Exception when the format of a value is invalid
    """
    pass


class PassException(ActionException):
    """
    Exception when the anonymize function must be skipped
    """
    pass
