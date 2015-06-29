#!/usr/bin/env bash

# Update and upgrade the package
apt-get update
apt-get upgrade -y

# Production
apt-get install python-pip -y
apt-get install tshark -y
pip install enum
pip install scapy
pip install python-magic
pip install netaddr
pip install tld
pip install hexdump
pip install datadiff
pip install dnspython


# Developpment
apt-get install git -y
apt-get install python-dev -y
apt-get install nodejs -y
apt-get install npm -y
apt-get install nodejs-legacy -y
npm install -g bower

cd projects/default/report/resources

# Install report dependency
bower install --config.interactive=false --allow-root

# Remove DNS layer in Scapy
rm /usr/local/lib/python2.7/dist-packages/scapy/layers dns.*
