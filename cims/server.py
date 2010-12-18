import SimpleHTTPServer
import SocketServer

import hacks
import app.translator
import app.mysql
import config
import simplejson as json

import os
import sys
import cgi
import urlparse

class Handler(SimpleHTTPServer.SimpleHTTPRequestHandler):
	def do_GET(self):
		self.send_response(200)
		self.send_header('Content-type','text/html')
		self.end_headers()
		
		#parse the query string
		qs = dict()
		if (self.path.find("?") != -1):
			qs = cgi.parse_qs(self.path.split("?")[1])
		
		ret = "[]"
		if ("input" in qs):
			if ("aggressive" in qs):
				app.translator.beAggressive = (qs["aggressive"][0] == "1")
			else:
				app.translator.beAggressive = False
			
			ret = json.dumps(app.translator.translate(qs["input"][0]))
		
		if ("callback" in qs):
			ret = qs["callback"][0] + "(" + ret + ")"
		
		self.wfile.write(ret)
		
		#close the database connection, otherwise it drops and things go haywire
		app.mysql.mysql.getInstance().close()

#do our config on launch
config.do()

#run that server -- even if we fork, we're still attached to an SSH session...so w/e
if (os.fork() == 0):
	os.chdir('/')
	os.umask(027)
	os.setsid()
	
	server = SocketServer.TCPServer(("", config.config.getint("deutsch", "cimsServerPort")), Handler)
	server.serve_forever()
else:
	sys.exit(0)
