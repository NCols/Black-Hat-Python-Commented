#!/usr/bin/env python

import socket

target_host = "www.google.com"
target_port = 80

# Create a socket object
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# The AF_INET parameter is saying we are going to use a standard IPv4 address or hostname
# SOCK_STREAM indicates that this will be a TCP client

# Connect the client
client.connect((target_host, target_port))

# Send some data
client.send("GET / HTTP/1.1\r\nHost: google.com\r\n\r\n")

# Receive some data (here in 4096 bytes chunks)
response = client.recv(4096)

print(response)
