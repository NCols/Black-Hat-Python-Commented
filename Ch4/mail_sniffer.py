#!/usr/bin/env python
#! -*- coding:utf-8 -*-

from scapy.all import *

# Our packet callback
def packet_callback(packet):
	print(packet.show())

# Let's fire up our sniffer
sniff(prn=packet_callback,count=1)