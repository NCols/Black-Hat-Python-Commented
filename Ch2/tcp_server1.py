#!/usr/bin/env python

import socket
import threading

bind_ip = "0.0.0.0"
bind_port = 9999

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server.bind((bind_ip,bind_port)) # We pass in the IP address and port we want the server to listen on

server.listen(5) # we tell the server to start listening with a maximum backlog of connections set to 5

print("[*] Listening on %s:%d" % (bind_ip,bind_port))

# This is our client-handling thread
# The handle_client w function performs the recv() and then sends a simple message back to the client
def handle_client(client_socket):
    # Print out what the client sends
    request = client_socket.recv(1024)

    print("[*] Received: %s" % request)

    # Send back a packet
    client_socket.send("ACK!")

    client_socket.close()


# We then put the server into its main loop, where it is waiting for an incoming connection
while True:
    client,addr = server.accept() # When a client connects, we receive the client socket into the client variable, and the remote connection details into the addr variable

    print("[*] Accepted connection from: %s:%d" % (addr[0],addr[1]))

    # We spin up our client thread to handle incoming data
    client_handler = threading.Thread(target=handle_client,args=(client,))
    client_handler.start()
