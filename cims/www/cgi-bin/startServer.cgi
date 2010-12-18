#!/usr/local/bin/python2.4

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
