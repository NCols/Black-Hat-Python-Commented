#!/usr/bin/env python

import socket

target_host = "127.0.0.1"
target_port = 80

client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Send some data
client.sendto("AAABBBCCC",(target_host,target_port))

# Receive some data
data, addr = client.recvfrom(4096) # It returns both the data and the details of the remote host and port

print(data)
print(addr)
