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


from sirano.action import Action
from sirano.exception import ExplicitDropException


class ICMPFilterTypeAction(Action):
    """
    Drop the entire packet explicitly it the ICMP type is not in the following list.

    Types to accept :
    --------------
    Echo Reply
    Echo Request
    Time Exceeded
    Destination Unreachable
    """

    name = "icmp-filter-type"

    types = {0: "echo-reply",
             3: "dest-unreach",
             8: "echo-request",
             11: "time-exceeded"}
    """Types to accept"""

    def discover(self, value):
        if int(value) not in self.types.keys():
            raise ExplicitDropException("value = '{}'".format(value))

    def anonymize(self, value):
        if int(value) not in self.types.keys():
            raise ExplicitDropException("value = '{}'".format(value))
        return value

    def __init__(self, app):
        super(ICMPFilterTypeAction, self).__init__(app)
