#!/usr/local/bin/python2.4
#
# Copyright (c) 2010 Andrew Stone
#
# This file is part of of Verbinator.
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

os.chdir("/home/shasha/verbinator.d/deutsch")
sys.path.append("/home/shasha/verbinator.d/deutsch")

import config
config.do()

#I don't know why tcsh doesn't like redirection...so just default to bash
bash = '''"bash -c 'nohup python /home/shasha/verbinator.d/deutsch/cims/server.py < /dev/null > /dev/null 2>&1'"'''

#wait for the server to spool up before we return the request
subprocess.Popen(
	#double ssh -- doesn't work otherwise...otherwise, ssh just complains, so double ssh to make it be quiet as the request
	#will then be masked by another server and look like a real ssh connection, not one from a stripped-down cgi-bin
	["ssh", "doowop7.cs.nyu.edu", "ssh", config.config.get("deutsch", "cimsServerHost") + " " + bash],
	stdout=subprocess.PIPE,
	stderr=subprocess.PIPE
).communicate()
