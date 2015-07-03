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
from sirano.plugins.actions.sip_p_charging_vector import SIPPChargingVectorAction


class SIPPChargingVectorActionTest(unittest.TestCase):
    """Unit tests for domain-name action plugin"""

    correct_samples = [
        "icid-value=6e903f84e4c1f5f22284be579a79a92471c034",
        "icid-value=1234bc9876e;icid-generated-at=192.0.6.8",
        "icid-value=1234bc9876e;icid-generated-at=192.0.6.8;orig-ioi=home1.net",
        "icid-value=ed210424-2ae0-1b21-91ba-000e0cb32bd9;icid-generated-at=192.0.6.8"
    ]

    def test_re_p_charging_vector(self):
        regex = SIPPChargingVectorAction.re_p_charging_vector

        # Correct sample 1
        match = regex.match(self.correct_samples[0])
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('ip'))
        self.assertIsNone(match.group('domain'))

        # Correct sample 2
        match = regex.match(self.correct_samples[1])
        self.assertIsNotNone(match)
        self.assertEqual(match.group('ip'), "192.0.6.8")
        self.assertIsNone(match.group('domain'))

        # Correct sample 3
        match = regex.match(self.correct_samples[2])
        self.assertIsNotNone(match)
        self.assertEqual(match.group('ip'), "192.0.6.8")
        self.assertEqual(match.group('domain'), "home1.net")

        # Correct sample 4
        match = regex.match(self.correct_samples[3])
        self.assertIsNotNone(match)
        self.assertEqual(match.group('ip'), "192.0.6.8")
        self.assertIsNone(match.group('domain'))