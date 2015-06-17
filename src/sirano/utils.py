# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>
import os
import errno

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
