import ConfigParser

config = ConfigParser.SafeConfigParser()

def do():
	global config
	config.read("config.ini")
