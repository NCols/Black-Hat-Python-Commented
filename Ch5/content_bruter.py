#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    import urllib.request as urllib2
except ImportError:
    import urllib2
import threading
try: 
    import queue
except ImportError:
    import Queue as queue
try:
    from urllib import quote  # Python 2.X
except ImportError:
    from urllib.parse import quote  # Python 3+
import sys

threads = 10
target_url = "http://testphp.vulnweb.com"
wordlist_file = "wordlist.txt"
resume = None
user_agent = "Mozilla/5.0 (X11; Linux x86_64; rv:19.0) Gecko/20100101 Firefox/19.0"

def build_wordlist(wordlist_file):
	# Read in the word list
	fd = open(wordlist_file, "rb")
	raw_words = fd.readlines()
	fd.close()
	
	found_resume = False
	words = queue.Queue()
	
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

"""
We want some basic functionality to be available to our brute-forcing
script. The first is the ability to apply a list of extensions to test for when
making requests. In some cases, you want to try not only the /admin directly
for example, but admin.php, admin.inc, and admin.html.
"""

def dir_bruter(word_queue,extensions=None):
	while not word_queue.empty():
		attempt = word_queue.get()
		attempt_list = []
		
		# Check to see if there's a file extension; if not
		# it's a directory path we're bruting
		if "." not in str(attempt):
			attempt_list.append("/%s/" % attempt) # ex site.com/admin/
		else:
			attempt_list.append("/%s" % attempt) # ex site.com/admin.php
		
		# If we want to brute force extensions, we add each extension to each word
		# in the list
		if extensions:
			for extension in extensions:
				attempt_list.append("/%s%s" % (attempt,extension))
		
		# Iterate over our list of attempts
		for brute in attempt_list:
			
			url = "%s%s" % (target_url, quote(brute)) # Build full url
			
			try:
				headers = {}
				headers['User-agent'] = user_agent
				r = urllib2.Request(url,headers=headers)
				
				response = urllib2.urlopen(r)
				
				# If response code is 200, we ouput the url
				if len(response.read()):
					print("[%d] => %s" % (response.code, url))
			
			# If we receive anything else than a 404, we also output it,
			# as it could potentially be something interesting for an attacker.
			except urllib2.URLError as e:
				if hasattr(e,'code') and e.code != 404:
					print("!!! %d => %s" % (e.code,url))
				# A check can be put in place to verify your script is working but just not finding anything:
				#else:
				#	print("[-] %s not found" % url)
				
				pass
			
			
# Setup our word list
print("[-] Building word queue...")
word_queue = build_wordlist(wordlist_file)
print("[*] Word queue built.")
extensions = [".php",".bak",".orig",".inc"]


for i in range(threads):
	print("Spawning thread: %d" % i)
	t = threading.Thread(target=dir_bruter, args=(word_queue,extensions,))
	t.start()
