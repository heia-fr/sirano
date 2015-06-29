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


class EmailAction(Action):
    """Action plugin for email addresses"""

    name = "email"

    def __init__(self, app):
        super(EmailAction, self).__init__(app)

        self.domain = self.app.manager.data.get_data('domain')
        self.name = self.app.manager.data.get_data('name')

    def discover(self, value):
        v = value.split('@')

        user = v[0]
        domain = v[1]

        self.domain.add_value(domain)
        self.name.add_value(user)

    def anonymize(self, value):
        v = value.split('@')

        user = v[0]
        domain = v[1]

        value = value.replace(user, self.name.get_replacement(user))
        value = value.replace(domain, self.domain.get_replacement(domain))

        return value



