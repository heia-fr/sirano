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
from sirano.plugins.actions.sip_identity import SIPIdentityAction


class SIPIdentityActionTest(unittest.TestCase):
    """Unit tests for domain-name action plugin"""

    def test_re_sip_identity(self):
        """
        Test the regular expression sip_identity
        :return:
        """
        regex = SIPIdentityAction.re_sip_identity

        # Correct sample 1
        sample = '"+41123445567" <sip:+41123445567@10.30.20.10>;tag=0018b9ead8a303640712c3ae-8391dc69'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "+41123445567")
        self.assertEqual(match.group('user'), "+41123445567")
        self.assertEqual(match.group('host'), "10.30.20.10")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 2
        sample = 'Alice <sip:alice@atlanta.com>;tag=1928301774'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Alice")
        self.assertEqual(match.group('user'), "alice")
        self.assertEqual(match.group('host'), "atlanta.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 3
        sample = 'sip:+12125551212@phone2net.com;tag=887s'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "+12125551212")
        self.assertEqual(match.group('host'), "phone2net.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 4
        sample = 'Anonymous <sip:c8oqz84zk7z@privacy.org>;tag=hyh8'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Anonymous")
        self.assertEqual(match.group('user'), "c8oqz84zk7z")
        self.assertEqual(match.group('host'), "privacy.org")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 5
        sample = '"Bob" <sips:bob@biloxi.com> ;tag=a48s'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Bob")
        self.assertEqual(match.group('user'), "bob")
        self.assertEqual(match.group('host'), "biloxi.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 6
        sample = '"" <sips:bob@biloxi.com> ;tag=a48s'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "bob")
        self.assertEqual(match.group('host'), "biloxi.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 7
        sample = 'sip:alice@atlanta.com;transport=tcp'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "alice")
        self.assertEqual(match.group('host'), "atlanta.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 8
        sample = 'sip:alice@atlanta.com;transport=udp;tag=hyh8'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "alice")
        self.assertEqual(match.group('host'), "atlanta.com")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 9
        sample = '<sip:10.10.10.10:5060;transport=udp>;+av-dse-enh=missed'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertIsNone(match.group('user'))
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 10
        sample = '"Thierry" <sip:123@10.10.10.10:5060>;tag=5805b8754b;epid=SC65162f'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Thierry")
        self.assertEqual(match.group('user'), "123")
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 11
        sample = '"Thierry" <sip:123@10.10.10.10:5060;maddr=192.168.0.0>;tag=5805b8754b;epid=SC65162f'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Thierry")
        self.assertEqual(match.group('user'), "123")
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertEqual(match.group('maddr'), "192.168.0.0")
        self.assertIsNone(match.group('devicename'))

        # Correct sample 12
        sample = '"Thierry" <sip:123@10.10.10.10:5060;transport=udp>;expires=3600'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertEqual(match.group('display'), "Thierry")
        self.assertEqual(match.group('user'), "123")
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 13
        sample = 'sip:+41123445567@10.10.10.10:5060;user=phone;transport=tcp'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "+41123445567")
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertIsNone(match.group('maddr'))
        self.assertIsNone(match.group('devicename'))

        # Correct sample 14
        sample = '<sip:cd2894a7-ac35-b222-f20f-310c67debb28@10.10.10.10:49558;transport=tcp>' \
                 ';+sip.instance="<urn:uuid:00000000-0000-0000-0000-0018b9ea45a3>"' \
                 ';+u.sip!devicename.ccm.cisco.com="ABC001234545656789";+u.sip!model.ccm.cisco.com="308"'
        match = regex.match(sample)
        self.assertIsNotNone(match)
        self.assertIsNone(match.group('display'))
        self.assertEqual(match.group('user'), "cd2894a7-ac35-b222-f20f-310c67debb28")
        self.assertEqual(match.group('host'), "10.10.10.10")
        self.assertEqual(match.group('devicename'), "ABC001234545656789")
