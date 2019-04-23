#!usr/bin/env python
#! -*- coding: utf-8 -*-

import threading
import time
from netaddr import IPNetwork,IPAddress
import socket
import os
import struct
from ctypes import *

# Host to listen on
host = "192.168.1.29"

# Subnet to target
subnet = "192.168.1.0/24"

# We define a simple string signature so that we can
# test that the responses are coming from UDP packets
# that we sent originally
magic_message = "PYTHONRULES!"

# Our udp_sender function simply takes in a subnet
# that we specify at the top of our script, iterates
# through all IP addresses in that subnet, and fires
# UDP datagrams at them
def udp_sender(subnet,magic_message):
	time.sleep(5)
	sender = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	for ip in IPNetwork(subnet):
		try:
			sender.sendto(magic_message,("%s" % ip,65212))
		except:
			pass

# Our IP header
class IP(Structure):
    _fields_ = [
        ("ihl",     c_ubyte, 4),
        ("version", c_ubyte, 4),
        ("tos",     c_ubyte, 4),
        ("len",     c_ushort),
        ("id",      c_ushort),
        ("offset",  c_ushort),
        ("ttl",     c_ubyte),
        ("protocol_num",c_ubyte),
        ("sum",     c_ushort),
        ("src",     c_uint, 32), # BHP says to put c_ulong here but doesn't work on x_64 Linux.
        ("dst",     c_uint, 32)  # Stackoverflow solution: switch c_ulong to c_uint:32)
    ]

    def __new__(self, socket_buffer=None):
        return self.from_buffer_copy(socket_buffer)

    def __init__(self, socket_buffer=None):

        # Map protocol constats to their names
        self.protocol_map = {1:"ICMP", 6:"TCP", 17:"UDP"}

        # Human readable IP addresses
        self.src_address = socket.inet_ntoa(struct.pack("<L", self.src))
        self.dst_address = socket.inet_ntoa(struct.pack("<L", self.dst))

        # Human readable protocol
        try:
            self.protocol = self.protocol_map[self.protocol_num]
        except:
            self.protocol = str(self.protocol_num)

# Let's also create an ICMP structure to allow us to decode ICMP information
class ICMP(Structure):
	_fields_ = [
		("type",		c_ubyte),
		("code",		c_ubyte),
		("checksum",	c_ushort),
		("unused",		c_ushort),
		("next_hop_mtu",c_ushort)
	]

	def __new__(self, socket_buffer):
		return self.from_buffer_copy(socket_buffer)

	def __init__(self, socket_buffer):
		pass

# Start sending packets
t = threading.Thread(target=udp_sender,args=(subnet,magic_message))
t.start()

# If we're using Linux, specify that we want to sniff the ICMP protocol
if os.name == "nt":
    socket_protocol = socket.IPPROTO_IP
else:
    socket_protocol = socket.IPPROTO_ICMP

sniffer = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket_protocol)

sniffer.bind((host,0))
sniffer.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)

# If Windows, turn on promiscuous mode
if os.name == "nt":
    sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_ON)

try:
    while True:

        # Read in a packet
        raw_buffer = sniffer.recvfrom(65565)[0]

        # Create an IP header from the first 20 bytes of the buffer
        ip_header = IP(raw_buffer[0:20])

        # Print out the protocol that was detectd and the hosts
        print("Protocol: %s %s -> %s" % (ip_header.protocol, ip_header.src_address, ip_header.dst_address))

		# When the main packet-receiving loop determines
		# that we have received an ICMP packet, we calculate the offset in the raw
		# packet where the ICMP body lives and then create our buffer and
		# print out the type and code fields. The length calculation is based on the
		# IP header ihl field, which indicates the number of 32-bit words (4-byte
		# chunks) contained in the IP header. So by multiplying this field by 4, we
		# know the size of the IP header and thus when the next network layer —
		# ICMP in this case — begins.


		# If it is ICMP, we want it
        if ip_header.protocol == "ICMP":

			# Calculate where our ICMP packet starts
			offset = ip_header.ihl *4

			buf = raw_buffer[offset:offset+sizeof(ICMP)]

			# Create out ICMP structure
			icmp_header = ICMP(buf)

			#print("ICMP -> Type: %d - Code: %d" % (icmp_header.type, icmp_header.code))

			# Let's check for the TYPE and CODE 3
			if icmp_header.code == 3 and icmp_header.type == 3:

				# If we detect the anticipated ICMP message,
				# we first check to make sure that the ICMP response
				# is coming from within our target subnet
				if IPAddress(ip_header.src_address) in IPNetwork(subnet):

					# Make sure it has our magic message in it
					if raw_buffer[len(raw_buffer)-len(magic_message):] == magic_message:
						# If all our checks have passed, then print out the
						# source IP address of where the ICMP message originated
						print("Host is Up: %s" % ip_header.src_address)


except KeyboardInterrupt:
	# If Windows, turn off promiscuous mode
    if os.name == "nt":
        sniffer.ioctl(socket.SIO_RCVALL, socket.RCVALL_OFF)
