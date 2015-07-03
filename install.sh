#!/usr/bin/env bash
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

################################################################################
# Sirano Installation Script
################################################################################
#
# This script is tested on Ubuntu 14.04 LTS (Trusty Tahr)
#
################################################################################

# Update and upgrade the package
apt-get update
apt-get upgrade -y

# Ubuntu Package
apt-get install python-dev -y
apt-get install python-pip -y
apt-get install tshark -y
apt-get install git -y
apt-get install nodejs -y
apt-get install npm -y
apt-get install nodejs-legacy -y
npm install -g bower

# Install Python packages
pip install -r requirements.txt

# Install report dependency
( cd projects/default/report/resources && bower install --config.interactive=false --allow-root)

# Set execution permission for user and group
chmod a+x sirano.py

# Bug fix for the Scapy RTP Layer
sed -i "s/'payload'/'payload_type'/g" /usr/local/lib/python2.7/dist-packages/scapy/layers/rtp.py
