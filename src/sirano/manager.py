# -*- coding: utf-8 -*-
#
# Copyright 2015 Loic Gremaud <loic.gremaud@grelinfo.ch>


class Manager(object):
    """Superclass for all managers"""

    name = None
    """The name of the manager, this class attribute must be declared in subclasses"""

    def __init__(self, app):
        """
        This initializer method must be called by subclasses

        :param app: The application instance
        :type app: App
        """
        self.app = app
        """The application instance"""

        self.conf = app.conf.setdefault(self.name, dict())
        """The manager configuration given by the YAML configuration file"""

        self.report = app.report.setdefault(self.name, dict())
        """
        The report data for the JSON file
        :type: dict[str, object]
        """

    def configure(self):
        """Configure the manager after all the others are initialized"""
        raise NotImplementedError