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

import re

from sirano.action import Action


class SIPCallIDAction(Action):
    """Action plugin for the field Call-ID of the SIP protocol"""

    name = "sip-call-id"

    call_id = re.compile(r"^[^@]*(@(?P<host>.*))?$")
    """The regular expression for a Call-ID field"""

    def __init__(self, app):
        super(SIPCallIDAction, self).__init__(app)

    def discover(self, value):

        call_id = self.call_id.match(value)

        if call_id is None:
            self.app.log.error("action:sip-call-id: Unknown format for '{}'".format(value))
            return

        host = call_id.group('host')

        if host is not None:
            self.app.manager.data.add_value(host)

    def anonymize(self, value):

        call_id = self.call_id.match(value)

        if call_id is None:
            self.app.log.error("action:sip-call-id: Unknown format for '{}'".format(value))
            return ''

        host = call_id.group('host')

        if host is not None:
            return value.replace(host, self.app.manager.data.get_replacement(host))

        else:
            return value

