#
# This file is part of Verbinator.
# 
# Verbinator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Verbinator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Verbinator.  If not, see <http://www.gnu.org/licenses/>.
#
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
