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

Tested on Ubuntu 14.04 LTS (Trusty Tahr)

```
sudo chmod u+x install.sh
sudo ./install.sh
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
