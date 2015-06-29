# Sirano

Network trace and log file anonymizer.

This version is for testing purposes.

## Features

### Supported file types

* Pcap packet-capture
* Text log file

### Supported protocols

* Ethernet
* IP
* TCP
* UDP
* ARP
* SIP
* SDP
* DNS <sup>[new]</sup>
* ICMP <sup>[new]</sup>

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

### Create a new project

```
python sirano.py create <project> 
```

* `project` : The name of the project folder to use

### Process a project

```
python sirano.py process <phase> <project> 
```

* `project` : The name of the project folder to use
* `phase` : The number of the phase to launch
  * `0` : Pass through all phases
  * `1` : The discover phase
  * `2` : The generation phase
  * `3` : The anonymisation phase
  * `4` : The validation phase
  
 
### Archive an existent project

```
python sirano.py archive <project> 
```

* `project` : The name of the project folder to use

### User documentation

The user documentation is in wiki at https://github.com/heia-fr/sirano/wiki
