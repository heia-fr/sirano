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
from sirano.exception import UnsupportedFormatException


class SIPIdentityAction(Action):
    """Action plugin for the field Identity of the SIP protocol"""

    name = 'sip-identity'

    re_sip_identity = re.compile(
        r'^"?(?P<display>.+?)??"?\s*<?sips?:(?:(?P<user>.+)@)?(?P<host>[^;\?]+?)(?::\d{1,6})?>?\s*(?:;(?:'
        r'tag|epid|expires|transport|user|\+av-dse-enh|[^;\?]*instance|[^;\?]*model|[^;\?=]*devicename|video|audio|'
        r'ms-opaque|privacy|screen|reason|counter'
        r')[^;\?]*|;maddr=(?P<maddr>[\d\.]+)|;[^;\?=]*="(?P<devicename>[^;\?]*)"|>)*$',
        re.IGNORECASE)
    """
    Regex for SIP URI;reason=unconditional;privacy=off;screen=yes
    """

    def __init__(self, app):
        super(SIPIdentityAction, self).__init__(app)

    def anonymize(self, value):
        match = self.re_sip_identity.match(value)
        if match is None:
            raise UnsupportedFormatException("The regular expression does not match")
        display = match.group('display')
        user = match.group('user')
        host = match.group('host')
        maddr = match.group('maddr')
        devicename = match.group('devicename')
        if display is not None:
            value = value.replace(display, self.app.manager.data.get_replacement(display))
        if devicename is not None:
            value = value.replace(devicename, self.app.manager.data.get_data('name').get_replacement(devicename))
        if user is not None:
            value = value.replace(user, self.app.manager.data.get_replacement(user))
        if host is not None:
            value = value.replace(host, self.app.manager.data.get_replacement(host))
        else:
            UnsupportedFormatException("The SIP identity should have an host part")
        if maddr is not None:
            value = value.replace(maddr, self.app.manager.data.get_data('ip').get_replacement(maddr))
        return value

    def discover(self, value):
        match = self.re_sip_identity.match(value)
        if match is None:
            raise UnsupportedFormatException("The regular expression does not match")
        display = match.group('display')
        user = match.group('user')
        host = match.group('host')
        maddr = match.group('maddr')
        devicename = match.group('devicename')
        if devicename is not None:
            self.app.manager.data.get_data('name').add_value(devicename)
        if display is not None:
            self.app.manager.data.add_value(display)
        if user is not None:
            self.app.manager.data.add_value(user)
        if host is not None:
            self.app.manager.data.add_value(host)
        else:
            UnsupportedFormatException("The SIP identity should have an host part")
        if maddr is not None:
            self.app.manager.data.get_data('ip').add_value(maddr)
        return value
