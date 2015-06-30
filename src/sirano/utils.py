# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>
import os
import errno
import datetime
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
        :type: sirano.app.App
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
        milliseconds = date.microseconds / 1000
        hours, milliseconds = divmod(milliseconds, 3600000)
        minutes, milliseconds = divmod(milliseconds, 60000)
        seconds, milliseconds = divmod(milliseconds, 1000)

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
        a_dict = {key : value}
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