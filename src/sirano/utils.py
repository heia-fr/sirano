# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>
import os
import errno
import datetime
from sirano.exception import DropException, ErrorDropException, ExplicitDropException
from vendor.pygpw import pygpw

class AppBase(object):
    """
    The base to inherit application instance
    """

    def __init__(self, app):
        """
        Constructor
        :param app: The application instance
        :type app: App
        """
        self.app = app
        """
        The application instance
        :type: App
        """

def makedirs(path):
    """Make directories without error if their already exist"""
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def word_generator(length):
    """
    Generate a pronounceable random word
    :param length: The length of the word to generate
    :type length: int
    :return: The random word generator
    :rtype: str
    """
    while True:
        label = pygpw.generate(numpasswords=1, passwordlength=length, substitute_rate=0, capitalize_rate=0)
        yield label[0][0:length]


def word_generate(length):
    """
    Generate a pronounceable random word
    :param length: The length of the word to generate
    :type length: int
    :return: The word
    :rtype: str
    """
    label = pygpw.generate(numpasswords=1, passwordlength=length, substitute_rate=0, capitalize_rate=0)
    return label[0][0:length]


def str_or_none(o):
    """
    Convert an object to a string or None
    :param o: The object
    :type o: object
    :return: The string or None if already None
    :rtype: str | None
    """
    if o is None:
        return None
    return str(o)


def date_to_json(date):
    """
    Date to json compatible date format
    :param date: The datetime or timedelta
    :type: datetime.timedelta | datetime.datetime
    :return: The json string format
    :rtype: str
    """
    if isinstance(date, datetime.timedelta):
        timedeltat_split = str(date).split(':')
        hours = int(timedeltat_split[0])
        minutes = int(timedeltat_split[1], 10)
        seconds_split = timedeltat_split[2].split('.')
        seconds = seconds_split[0]
        milliseconds = int(seconds_split[1][:3], 10)

        # DEBUG
        # print("Debug: timedelta = '{}' conversion = '{}h {}min {}sec {}ms'".format(date, hours, minutes, seconds,
        #                                                                            milliseconds))

        if hours:
            return "{} h {} min".format(hours, minutes)
        elif minutes:
            return "{} min {} sec".format(minutes, seconds)
        elif seconds:
            return "{} sec {} ms".format(seconds, milliseconds)
        else:
            return "{} ms".format(milliseconds)
    elif isinstance(date, datetime.datetime):
        return date.strftime("%Y-%m-%d %H:%M:%S")


def find_one_dict_by_key(list_of_dict, key, value, create=False):
    """
    Get the first entry from a list of dict that have a key with the specified value
    :param list_of_dict: The list of dict
    :type list_of_dict: list[dict]
    :param key: The key to check
    :type key: object
    :param value: The value must be not None
    :type value: object
    :param create: If True creates the dict if it not exists
    :return: The founded or created dict or None if creates is False
    """
    for a_dict in list_of_dict:
        if a_dict.get(key) == value:
            return a_dict
    if create:
        a_dict = {key: value}
        list_of_dict.append(a_dict)
        return a_dict
    return None


def force_setdefault(a_dict, key, default):
    """
    Same as setdefault for dictionnary but if value is None it set the default too
    :param a_dict: The dictionnary
    :type: dict
    :param key: The key
    :param default: The default value, must be not None
    :return: The reference to the value
    """
    if a_dict.get(key) is None:
        a_dict[key] = default
    return a_dict[key]


def raise_drop_exception(exception, information):
    """
    Handling exception and generate DropException if necessary
    :param exception: The exception
    :type: Exception
    :param information: Additional information to add before the message
    :raise DropException: More information is added to the exception that was already a DropException
    :raise ErrorDropException: A ErrorDropException is generated from an ordinary Exception
    """
    if isinstance(exception, DropException):
        # Raise the same exception type to preserve ImplicitDropException, ErrorDropException or ExplicitDropException
        raise type(exception)("{}, {}".format(information, exception.message))
    else:
        # Raise a ErrorDropException with information about the original exception type and message
        raise ErrorDropException("{}, exception = '{}', message='{}'".format(
            information, type(exception).__name__, exception.message))

def read_by_n_lines(f, n):
    """
    Read n line from a the file descripto f
    :param f: The file descriptor
    :type f: File
    :param n: The number of lines to read
    :type n: int
    :return: A generator with an list of tuple with the line number and the line
    :rtype: list[list[int, str]]
    """
    lines = list()
    for line_number, line in enumerate(f):
        lines.append((line_number, line))
        if len(lines) == n:
            yield lines
            lines = list()
    if len(lines) != 0:
        yield lines
