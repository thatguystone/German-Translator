import sys
import os
import ConfigParser

config = ConfigParser.SafeConfigParser()

def do():
	global config
	config.read(os.path.abspath(os.path.dirname(__file__)) + "/config.ini")
