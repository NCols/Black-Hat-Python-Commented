#!/usr/bin/env python
# -*- coding: utf-8 -*-

import Queue
import threading
import os
import urllib2

threads = 10

"""
We begin by defining the remote target website and the local directory
into which we have downloaded and extracted the web application.
We also create a simple list of file extensions that we are not interested in
finger­printing.
"""
target = "http://catherinejoie.be"
directory = "/home/nc/Documents/wordpressCath"
filters = [".jpg",".gif",".png",".css"]

os.chdir(directory)

# The web_paths variable is our Queue object where we will
# store the files that we’ll attempt to locate on the remote server.
web_paths = Queue.Queue()

"""
We then use the os.walk function to walk through all of the files and directories in the local web
application directory. As we walk through the files and directories, we’re
building the full path to the target files and testing them against our filter
list to make sure we are only looking for the file types we want. For each
valid file we find locally, we add it to our web_paths Queue.
"""
for r,d,f in os.walk("."):
    for files in f:
        remote_path = "%s/%s" % (r,files)
        if remote_path.startswith("."):
            remote_path = remote_path[1:]
        if os.path.splitext(files)[1] not in filters:
            web_paths.put(remote_path)

def test_remote():
    while not web_paths.empty():
        # On each iteration, while there's data in the queue, we grab one entry (path) after the other
        path = web_paths.get()
        # We attempt to retrieve the file
        url = "%s%s" % (target,path)
        request = urllib2.Request(url)

        # If we successfully retrieve it, we output the HTTP status code
        # and the full path to the file
        try:
            response = urllib2.urlopen(request)
            content = response.read()

            print("[%d] => %s" % (response.code, path))
            response.close()

        # If the file is not found or cannot be accessed, urllib2 will throw an error
        # which we handle so the loop can continue executing
        except urllib2.HTTPError as error:
            print("[!!] Failed => Error code %s" % error.code)
            pass

for i in range(threads):
    print("Spawning thread: %d" % i)
    t = threading.Thread(target=test_remote)
    t.start()
