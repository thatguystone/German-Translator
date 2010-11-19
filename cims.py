#!/usr/bin/python2.4
# -*- coding: utf-8 -*-

from cims import hacks
import config

def main():
	setup()
	
	from cli import route
	route.router().go()
	
def setup():
	"""Sets up all the connections to everything"""
	config.do()

if (__name__ == "__main__"):
	main()
