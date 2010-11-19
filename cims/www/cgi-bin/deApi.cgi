#!/usr/bin/python2.4

print "Content-type: text/html\n\n"

import os
import sys

#let's cd into the translator
os.chdir("/home/abs407/deutsch")

#the actual code
sys.path.append("/home/abs407/deutsch")

from cims import hacks

import cims.cgiHandler
cims.cgiHandler.go()
