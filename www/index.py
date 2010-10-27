import sys
import os
import json
from mod_python import apache
from mod_python.util import parse_qsl

sys.path.append(os.path.abspath(os.path.dirname(__file__) + "/../app"))
sys.path.append(os.path.abspath(os.path.dirname(__file__)))
import translator
import config

class RequestHandler(object):
	def __init__(self, req):
		req.content_type = 'text/html'
		self.__setupQueryString(req)
		self.__setupPath(req)
		self.req = req
	
	def __setupQueryString(self, req):
		self.qs = dict()
		for key, value in parse_qsl(req.args):
			self.qs[key] = value
		
		self.jsonp = ("callback" in self.qs)
	
	def __setupPath(self, req):
		if ("requestPath" in self.qs):
			path = self.qs["requestPath"]
			del self.qs["requestPath"]
			self.path = path.split("/")
		else:
			self.path = []
	
	def process(self):
		#check the first path item to see what we're processing
		if (len(self.path) == 0):
			pass #go to the index page
		elif (self.path[0] == "api"):
			ret = []
			if ("input" in self.qs):
				for t in translator.translate(self.qs["input"]):
					ret.append({"en": t["en"], "de": t["de"]})
			
			if (self.jsonp):
				self.req.write(self.qs["callback"] + "(");
			
			self.req.write(json.dumps(ret))
			
			if (self.jsonp):
				self.req.write(");");
		else:
			pass #nothing to handle, yet
			
		return 0

def handler(req):
	return RequestHandler(req).process()

def setup():
	config.do()

setup()