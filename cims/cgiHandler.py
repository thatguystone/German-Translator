import sys
import os
import simplejson as json
import app.translator
import config

import cgi
import urlparse

class RequestHandler(object):
	def __init__(self):
		self.__setupQueryString()
	
	def __setupQueryString(self):
		self.qs = dict()
		if ("QUERY_STRING" in os.environ):
			#this is deprecated, but then again, the server is running python2.4
			self.qs = cgi.parse_qs(os.environ["QUERY_STRING"])
		
		self.jsonp = ("callback" in self.qs)
	
	def process(self):
		ret = []
		if ("input" in self.qs):
			ret = app.translator.translate(self.qs["input"][0])
		
		if (self.jsonp):
			print self.qs["callback"] + "("
		
		print json.dumps(ret)
		
		if (self.jsonp):
			print ");"

def go():
	config.do()
	RequestHandler().process()
	#cgi.print_environ_usage()
