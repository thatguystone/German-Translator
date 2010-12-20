#!/usr/local/bin/python2.4
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
import subprocess
import sys, os

print "Content-type: text/html\n\n"

os.chdir("/home/abs407/deutsch")
sys.path.append("/home/abs407/deutsch")

#load our configuration so that we know on which server to start the stuff
import config
config.do()

#wait for the server to spool up before we return the request
subprocess.Popen(
	["ssh", "doowop7.cs.nyu.edu", "ssh " + config.config.get("deutsch", "cimsServerHost") + " \"nohup python /home/abs407/deutsch/cims/server.py < /dev/null > /dev/null 2>&1\""],
	stdout=subprocess.PIPE,
	stderr=subprocess.PIPE
).communicate()
