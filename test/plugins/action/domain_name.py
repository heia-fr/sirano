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

import unittest
from sirano.plugins.actions.domain_name import DomainNameAction
from sirano.plugins.actions.sip_p_charging_vector import SIPPChargingVectorAction


class DomainNameActionTest(unittest.TestCase):
    """Unit tests for domain-name action plugin"""

    correct_ptr_samples = [
        "115.42.16.172.in-addr.arpa.",
        "172.16.67.128"
    ]

    def test_re_p_charging_vector(self):
        regex = DomainNameAction.re_ptr

        # Correct sample 1
        match = regex.match(self.correct_ptr_samples[0])
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('ip'))
        self.assertEqual(match.group('ip_reversed'), '115.42.16.172')

        # Correct sample 2
        match = regex.match(self.correct_ptr_samples[1])
        self.assertIsNotNone(match)
        self.assertEqual(match.group('ip'), '172.16.67.128')
        self.assertIsNone(match.group('ip_reversed'))
