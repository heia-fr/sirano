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

from sirano.manager import Manager


class _ActionMetaclass(type):
    """Metaclass to create self-registering Action plugins """

    def __init__(cls, name, bases, attributes):
        """ Called when an Action plugin is imported """

        super(_ActionMetaclass, cls).__init__(name, bases, attributes)

        ac = ActionManager.action_classes

        if isinstance(ac, dict):
            name = attributes['name']
            if name in ac:
                raise ImportError("Action class with property name = '%s' already exists")
            else:
                ac[name] = cls
        else:
            ActionManager.action_classes = dict()


class ActionManager(Manager):
    """
    Manage both classes and the instances of plugins Action
    """

    name = 'action'
    action_classes = None
    """Imported Action plugins, the key contain the name and the value contain the class"""

    def __init__(self, app):
        Manager.__init__(self, app)

        self.actions = dict()

    def configure(self):
        self.app.log.debug("manager:action: Configured")

    def __create_action(self, name):
        try:
            a_cls = self.action_classes[name]
        except KeyError:
            __import__('sirano.plugins.actions.' + name)
            a_cls = self.action_classes[name]

        a = a_cls(self.app)

        self.actions[name] = a

        self.app.log.debug("manager:action: Create action '%s'", name)

        return a

    def get_action(self, name):
        try:
            return self.actions[name]
        except KeyError:
            return self.__create_action(name)


class Action:
    """
    Superclass for all actions
    """

    name = None
    """The name of the action, this class attribute must be declared in subclasses."""

    __metaclass__ = _ActionMetaclass

    def __init__(self, app):
        self.app = app
        """
        The instance of the application
        :type : App
        """

    def discover(self, value):
        """
        Discover the specified value

        This method must be implemented in subclasses.

        :param value: The value
        :type value: str
        """
        raise NotImplementedError("discover function in action '%s'", self.name)

    def anonymize(self, value):
        """
        Anonymize the specified value

        This method must be implemented in subclasses.

        :param value: The value
        :type value: str
        :return The anonymized value
        :rtype str
        """
        raise NotImplementedError("alter function in action '%", self.name)