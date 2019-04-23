#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
We’ll use a known behavior of most operating systems when handling
closed UDP ports to determine if there is an active host at a particular
IP address. When you send a UDP datagram to a closed port on a host,
that host typically sends back an ICMP message indicating that the port is
unreachable. This ICMP message indicates that there is a host alive because
we’d assume that there was no host if we didn’t receive a response to the
UDP datagram. It is essential that we pick a UDP port that will not likely be
used, and for maximum coverage we can probe several ports to ensure we
aren’t hitting an active UDP service.

We will be building the script both for Windows and Linux.

Accessing raw sockets in Windows is slightly different than on its Linux
brethren, but we want to have the flexibility to deploy the same sniffer
to multiple platforms. We will create our socket object and then deter-
mine which platform we are running on. Windows requires us to set some
additional flags through a socket input/output control (IOCTL), 1 which
enables promiscuous mode on the network interface. In our first example,
we simply set up our raw socket sniffer, read in a single packet, and then quit.
"""

import os
import socket

# Host to listen on
host = "192.168.1.29"

# Create a raw socket and bind it to the public interface
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP # We start by constructing our socket object with the parameters necessary for sniffing packets on our network interface
else:
    socket_protocol = socket.IPPROTO_ICMP

# The difference between Windows and Linux is that Windows will allow us to sniff all
# incoming packets regardless of protocol, whereas Linux forces us to spec-
# ify that we are sniffing ICMP. Note that we are using promiscuous mode,
# which requires administrative privileges on Windows or root on Linux.

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

sniffer.bind((host,0))

# We want IP headers included in the capture
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# If we're using Windows, we need to send an IOCTL to setup promiscuous mode
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

# Read a single packer
print(sniffer.recvfrom(65565))

# If we're using Windows, turn off promiscuous mode
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
