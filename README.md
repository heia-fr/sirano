# Sirano

Network trace and log file anonymizer.

This version is for testing purposes.

## Features

### Supported file types

* Pcap packet-capture
* Text log file <sup>[new]</sup>

### Supported protocols

* Ethernet
* IP
* TCP
* UDP
* ARP <sup>[new]</sup>
* SIP
* SDP
* DNS <sup>[coming soon]</sup>
* ICMP <sup>[coming soon]</sup>

### Supported data types

* MAC address
* IPv4 address
* Domain name
* Name

## Installation

### Vagrant

From the src folder :

```
vagrant up
```

### Ubuntu

Ubuntu 14.04 LTS (Trusty Tahr)

```
sudo apt-get update
sudo apt-get install python-pip -y
sudo apt-get install python-dev -y
sudo pip install enum
sudo pip install scapy
sudo pip install python-magic
sudo pip install netaddr
sudo pip install tld
sudo pip install hexdump
```

## Usage

From the src folder :

```
python sirano.py <project> <phase>
```

* `project` : The name of the project folder to use
* `phase` : The number of the phase to launch
  * `0` : Pass through all phases
  * `1` : The discover phase
  * `2` : The generation phase
  * `3` : The anonymisation phase
  * `4` : The validation phase

User documentation is coming soon...
