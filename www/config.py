import ConfigParser
import os

config = ConfigParser.SafeConfigParser()

def do():
	global config
	#use the config file that it outside of the web directory...don't want that getting around!
	config.read(os.path.abspath(os.path.dirname(__file__) + "/../config.ini"))
