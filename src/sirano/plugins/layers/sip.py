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

from scapy.fields import StrField
from scapy.layers.inet import TCP, UDP
from scapy.packet import Packet, bind_layers


class SDP(Packet):
    """
    A Scapy Layer for SDP Session Description Protocol
    """
    name = 'SDP Session Description Protocol'

    re_desc = re.compile(r"^(?P<type>[a-z])=(?P<value>[^\r]*)\r?\n$")
    """A regex for the type, value pair in a description"""

    def __init__(self, _pkt="", post_transform=None, _internal=0, _underlayer=None, **fields):

        self.descriptions = list()
        """Contains each descriptions lines, used to conserve line order, size and format"""

        super(SDP, self).__init__(_pkt, post_transform, _internal, _underlayer, **fields)

    def clone_with(self, payload=None, **kargs):
        """
        Overloaded to conserve descriptions attribute on clone

        :param payload: The payload of the layer
        :param kargs: Other extra arguments
        """
        pkt = super(SDP, self).clone_with(payload, **kargs)
        pkt.descriptions = self.descriptions

        return pkt

    def setfieldval(self, attr, val):

        if attr in self.fields:

            field = self.fields[attr]

            if isinstance(field, list):

                if not isinstance(val, list):
                    val = [val]

                for i in xrange(len(val)):
                    [v, l] = field[i]

                    l = l.replace(v, val[i])

                    self.fields[attr][i][0] = val[i]
                    self.fields[attr][i][1] = l

        super(SDP, self).setfieldval(attr, val)

    def getfieldval(self, attr):
        _, v = self.getfield_and_val(attr)
        return v

    def getfield_and_val(self, attr):

        if attr in self.fields:

            field = self.fields[attr]

            if isinstance(field, list):

                if len(field) == 1:
                    [v, _] = field[0]
                    return None, v

                f = list()
                for v, _ in field:
                    f.append(v)

                return None, f

        return super(SDP, self).getfield_and_val(attr)

    def do_dissect(self, s):

        lines = s.splitlines(True)

        for _ in xrange(len(lines)):
            line = lines.pop(0)

            desc = self.re_desc.match(line)

            t = desc.group('type')
            v = desc.group('value')

            field = [v, line]

            if t not in self.fields:
                self.fields[t] = list()

            self.fields[t].append(field)
            self.fieldtype[t] = StrField("", None)

            self.descriptions.append(field)

        return ''

    def self_build(self, field_pos_list=None):

        s = ''

        for _, l in self.descriptions:
            s += l

        return s


class SIPHeader(Packet):
    """
    A Scapy Layer for SIP Header

    This layer is used to access to all possible header fields.
    """

    name = 'SIP Header'

    re_header_field = re.compile(r"^(?P<field_name>[^:]*)\s*:\s*(?P<field_value>[^\r]*)\r?\n$")
    """A regex for the name, value pair in a SIP header field"""

    def __init__(self, _pkt="", post_transform=None, _internal=0, _underlayer=None, **fields):

        self.header_fields = list()
        """Contains each headers lines, used to conserve line order, size and format"""

        super(SIPHeader, self).__init__(_pkt, post_transform, _internal, _underlayer, **fields)

    def clone_with(self, payload=None, **kargs):
        """
        Overloaded to conserve header_fields attributes on clone

        :param payload: The payload of the layer
        :param kargs: Other extra arguments
        """

        pkt = super(SIPHeader, self).clone_with(payload, **kargs)
        pkt.header_fields = self.header_fields

        return pkt

    def setfieldval(self, attr, val):

        n = attr

        if n in self.fields:

            field = self.fields[n]

            if isinstance(field, list):

                if not isinstance(val, list):
                    val = [val]

                for i in xrange(len(val)):
                    [v, l] = field[i]

                    l = l.replace(v, val[i])

                    self.fields[n][i][0] = val[i]
                    self.fields[n][i][1] = l

        super(SIPHeader, self).setfieldval(attr, val)

    def getfieldval(self, attr):
        _, v = self.getfield_and_val(attr)
        return v

    def getfield_and_val(self, attr):

        n = attr

        if n in self.fields:

            field = self.fields[n]

            if isinstance(field, list):

                if len(field) == 1:
                    [v, _] = field[0]
                    return None, v

                f = list()
                for v, _ in field:
                    f.append(v)

                return None, f

        return super(SIPHeader, self).getfield_and_val(attr)

    def do_dissect(self, s):

        lines = s.splitlines(True)

        for _ in xrange(len(lines)):
            line = lines.pop(0)

            if line == '\r\n':
                break

            header_field = self.re_header_field.match(line)

            field_name = header_field.group('field_name')

            field_value = str(header_field.group('field_value'))

            field = [field_value, line]

            if field_name not in self.fields:
                self.fields[field_name] = list()

            self.fields[field_name].append(field)
            self.fieldtype[field_name] = StrField("", None)

            self.header_fields.append(field)

        body = ''.join(lines)

        return body

    def self_build(self, field_pos_list=None):

        s = ''

        for _, l in self.header_fields:
            s += l

        return s + '\r\n'


class SIPRequest(Packet):
    """
    Scapy SIP Request Layer

    This layer is used when the first line is a SIP Request
    """

    name = 'SIP Request'

    fields_desc = [
        StrField('Method', None),
        StrField('Request-URI', None),
        StrField('SIP-Version', None),
    ]

    def do_dissect(self, s):
        lines = str(s).splitlines(True)

        request_line = SIP.re_request_line.match(lines.pop(0))

        self.setfieldval('Method', request_line.group('method'))
        self.setfieldval('Request-URI', request_line.group('request_uri'))
        self.setfieldval('SIP-Version', request_line.group('sip_version'))

        return ''.join(lines)

    def self_build(self, field_pos_list=None):

        method = self.getfieldval('Method')
        request_uri = self.getfieldval('Request-URI')
        sip_version = self.getfieldval('SIP-Version')

        return "{} {} {}\r\n".format(method, request_uri, sip_version)


class SIPResponse(Packet):
    """
    Scapy SIP Response Layer

    This layer is used when the first line is a SIP Response
    """

    name = 'SIP Response'

    fields_desc = [
        StrField('SIP-Version', None),
        StrField('Status-Code', None),
        StrField('Reason-Phrase', None),
    ]

    def do_dissect(self, s):
        lines = str(s).splitlines(True)

        status_line = SIP.re_status_line.match(lines.pop(0))

        self.setfieldval('SIP-Version', status_line.group('sip_version'))
        self.setfieldval('Status-Code', status_line.group('status_code'))
        self.setfieldval('Reason-Phrase', status_line.group('reason_phrase'))

        return ''.join(lines)

    def self_build(self, field_pos_list=None):
        return "{} {} {}\r\n".format(
            self.getfieldval('SIP-Version'),
            self.getfieldval('Status-Code'),
            self.getfieldval('Reason-Phrase'))


class SIP(Packet):
    """
    Scapy SIP Layer

    This layer is used when the first line is a SIP Request or Request
    """

    name = "SIP"

    re_request_line = re.compile(r"^(?P<method>.*)\s(?P<request_uri>.*)\s(?P<sip_version>SIP/\d.\d)\r?\n$")
    re_status_line = \
        re.compile(r"^(?P<sip_version>SIP/\d.\d)\s(?P<status_code>\d\d\d)\s(?P<reason_phrase>[^\r]*)\r?\n$")

    def guess_payload_class(self, payload):

        start_line = payload.splitlines(True)[0]

        if self.re_request_line.match(start_line) is not None:
            return SIPRequest
        elif self.re_status_line.match(start_line) is not None:
            return SIPResponse

        return Packet.guess_payload_class(self, payload)

    def do_dissect(self, s):
        return s


bind_layers(TCP, SIP, dport=5060)
bind_layers(TCP, SIP, sport=5060)
bind_layers(UDP, SIP, dport=5060)
bind_layers(UDP, SIP, sport=5060)

bind_layers(SIPResponse, SIPHeader)
bind_layers(SIPRequest, SIPHeader)

bind_layers(SIPHeader, SDP, **{'Content-Type': 'application/sdp'})
