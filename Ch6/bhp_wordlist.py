#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
The trick to online password guessing is getting the right wordlist. You
can’t test 10 million passwords if you’re in a hurry, so you need to be able to
create a wordlist targeted to the site in question. Of course, there are scripts
in the Kali Linux distribution that crawl a website and generate a wordlist
based on site content. Though if you’ve already used Burp Spider to crawl
the site, why send more traffic just to generate a wordlist? Plus, those scripts
usually have a ton of command-line arguments to remember, so let's Burp do the heavy lifting.
"""

from burp import IBurpExtender
from burp import IContextMenuFactory

from javax.swing import JMenuItem
from java.util import List, ArrayList
from java.net import URL

import re
from datetime import datetime
from HTMLParser import HTMLParser

class TagStripper(HTMLParser):
	def __init__(self):
		HTMLParser.__init__(self)
		self.page_text = []

	# A helper TagStripper class will allow us
	# to strip the HTML tags out of the HTTP responses we process later on.
	# Its handle_data function stores the page text in a member variable. We
	# also define handle_comment because we want the words stored in developer
	# comments to be added to our password list as well. Under the covers,
	# handle_comment just calls handle_data (in case we want to change how we
	# process page text down the road).

	def handle_data(self, data):
		self.page_text.append(data)

	def handle_comment(self, data):
		self.handle_data(data)

	# The strip function feeds HTML code to the base class, HTMLParser, and
	# returns the resulting page text, which will come in handy later.

	def strip(self, html):
		self.feed(html)
		return " ".join(self.page_text)

class BurpExtender(IBurpExtender, IContextMenuFactory):
    def registerExtenderCallbacks(self, callbacks):
    	self._callbacks = callbacks
    	self._helpers = callbacks.getHelpers()
    	self.context = None
    	self.hosts = set()

    	# We initialize the set with everyone’s favorite password, “password”,
    	# just to make sure it ends up in our final list.
    	self.wordlist = set(["password"])

    	# We set up our extension
    	callbacks.setExtensionName("BHP Wordlist")
    	callbacks.registerContextMenuFactory(self)

    	return

    def createMenuItems(self, context_menu):
        self.context = context_menu
        menu_list = ArrayList()
        menu_list.add(JMenuItem("Create Wordlist", actionPerformed=self.wordlist_menu))

        return menu_list

    def wordlist_menu(self, event):

        # Grab the details of what the user clicked
        http_traffic = self.context.getSelectedMessages()

        for traffic in http_traffic:
            http_service = traffic.getHttpService()
            host = http_service.getHost()

            # We save the name of the responding host for later,
            # and then retrieve the HTTP response and feed it to
            # our get_words function.

            self.hosts.add(host)

            http_response = traffic.getResponse()

            if http_response:
                self.get_words(http_response)

        self.display_wordlist()
        return

    def get_words(self, http_response):

        headers, body = http_response.tostring().split('\r\n\r\n',1)

        # Skip non-text responses
        if headers.lower().find("content-type: text") == -1:
            return

        # Our TagStripper class strips the HTML code from the rest of the page text.
        tag_stripper = TagStripper()
        page_text = tag_stripper.strip(body)

        # We use regex to find all words starting with an alphabetic
        # character followed by two or more "word" characters.
        words = re.findall("[a-zA-Z]\w{2,}", page_text)

        for word in words:
            # Filter out long strings
            if len(word) <= 12:
                # Save in lowercase to the wordlist
                self.wordlist.add(word.lower())

        return

    # Now let’s round out the script by giving it the ability
    # to mangle and display the captured wordlist.
    def mangle(self, word):
        # The mangle function takes a base word and turns it into a
        # number of password guesses based on some common password creation
        # “strategies.” In this simple example, we create a list of suffixes to tack on the
        # end of the base word, including the current year.
        year = datetime.now().year
        suffixes = ["","1","!",year]
        mangled = []

        # Next we loop through each suffix and add it to the base word
        # to create a unique password attempt. We do another loop with
        # a capitalized version of the base word for good measure.
        for password in (word, word.capitalize()):
            for suffix in suffixes:
                mangled.append("%s%s" % (password,suffix))

        return mangled

    # In the display_wordlist function, we print a “John the
    # Ripper”–style comment to remind us which sites were used to generate
    # this wordlist. Then we mangle each base word and print the results.
    def display_wordlist(self):
        print("#!comment: BHP Wordlist for site(s) %s" % ", ".join(self.hosts))

        for word in sorted(self.wordlist):
            for password in self.mangle(word):
                print(password)

        return
