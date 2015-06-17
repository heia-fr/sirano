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
from sirano.exception import FormatException


class SIPIdentityAction(Action):
    """Action plugin for the field Identity of the SIP protocol"""

    name = 'sip-identity'

    re_sip_uri = re.compile(r"^sips?:((?P<user>[^;]*)@)?(?P<host>[^:;\?]+)(:(?P<port>\d+))?((;|\?)(?P<dparams>.*))?$")
    """
    Regex for SIP URI

    Tested with examples in the RFC3261:

        sip:alice@atlanta.com
        sip:alice:secretword@atlanta.com;transport=tcp
        sips:alice@atlanta.com?subject=project%20x&priority=urgent
        sips:1212@gateway.com
        sip:alice@192.0.2.4
        sip:atlanta.com;method=REGISTER?to=alice%40atlanta.com

    Not working with this specials cases:

        sip:alice;day=tuesday@atlanta.com
        sip:+1-212-555-1212:1234@gateway.com;user=phone

    """

    re_sip_identity = re.compile(
        r"^\"?(?P<display_name>(\s?[^\"\s<])+)?\"?\s*<?(?P<sip_uri>sips?:[^>;\?]*)>?\s*((;|\?)(?P<params>.*))?$")
    """
    Regex for SIP Identity

    Tested with examples in the RFC3261:

        "A. G. Bell" <sip:agb@bell-telephone.com> ;tag=a48s
        sip:+12125551212@server.phone2net.com;tag=887s
        Anonymous <sip:c8oqz84zk7z@privacy.org>;tag=hyh8;test=test
        The Operator <sip:operator@cs.columbia.edu>;tag=287447
        sip:+12125551212@server.phone2net.com
    """

    def __init__(self, app):
        super(SIPIdentityAction, self).__init__(app)

    def anonymize(self, value):

        sip_identity_m = self.re_sip_identity.match(value)

        if sip_identity_m is None:
            raise FormatException(self.name, value)

        display_name = sip_identity_m.group('display_name')
        sip_uri = sip_identity_m.group('sip_uri')

        sip_uri_m = self.re_sip_uri.match(sip_uri)

        if sip_uri_m is None:
            raise FormatException(self.name, value)

        if display_name is not None:
            value = value.replace(display_name, self.app.manager.data.get_data('name').get_replacement(display_name))

        # d = dict()

        user = sip_uri_m.group('user')

        if user is not None:
            value = value.replace(user, self.app.manager.data.get_replacement(user))

        host = sip_uri_m.group('host')
        value = value.replace(host, self.app.manager.data.get_replacement(host))

        return value

        # todo log parameters

    def discover(self, value):

        sip_identity = self.re_sip_identity.match(value)

        if sip_identity is None:
            self.app.log.error("action:sip-identity: unknown format for '%s'", value)
            return

        display_name = sip_identity.group('display_name')
        sip_uri = sip_identity.group('sip_uri')

        sip_uri = self.re_sip_uri.match(sip_uri)

        if sip_uri is None:
            raise FormatException(self.name, value)

        user = sip_uri.group('user')
        host = sip_uri.group('host')

        if display_name is not None:
            self.app.manager.data.get_data('name').add_value(display_name)

        if user is not None:
            self.app.manager.data.add_value(user)

        self.app.manager.data.add_value(host)



