#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
# We are just fetching the raw page here, no Javascript or
# other client-side languages will execute.
body = urllib2.urlopen("http://www.google.com") # Returns a file-like object that allows us to read back the body of what the remote web server returns
print(body.read())

"""
In most cases, however, you are going to want more finely grained
control over how you make these requests, including being able to define
specific headers, handle cookies, and create POST requests. urllib2 exposes
a Request class that gives you this level of control. Below is an example of
how to create the same GET request using the Request class and defining a
custom User-Agent HTTP header
"""

# The construction of a Request object is slightly different than our previous example
url = "http://www.duckduckgo.com"

# To create custom headers, we define a headers dictionary, which allows to
# then set the header key and value that we want to use (in this case, Duckbot)
headers = {}
headers['User-agent'] = "Duckbot"

# We then create our Request object and pass the url and the headers dictionary
request = urllib2.Request(url, headers=headers)
# And then pass the Request object to the urlopen function call.
# This returns a normal file-like object that we can use to read in the data
# from the remote website.
response = urllib2.urlopen(request)

print(response.read())
response.close()
