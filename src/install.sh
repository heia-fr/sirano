#!/usr/bin/env bash

# Update and upgrade the package
apt-get update
apt-get upgrade -y

# Production
apt-get install python-pip -y
apt-get install tshark -y
apt-get install git -y
apt-get install python-dev -y
apt-get install nodejs -y
apt-get install npm -y
apt-get install nodejs-legacy -y
npm install -g bower
pip install enum
pip install scapy
pip install python-magic
pip install netaddr
pip install tld
pip install hexdump
pip install datadiff
pip install dnspython
pip install pyyaml


# Install report dependency
( cd projects/default/report/resources && bower install --config.interactive=false --allow-root)

# Set execution permission for user and group
chmod gu+x sirano.py

# Bug fix
sed -i "s/'payload'/'payload_type'/g" /usr/local/lib/python2.7/dist-packages/scapy/layers/rtp.py
