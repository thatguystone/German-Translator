#!/usr/bin/env python2.6
# -*- coding: utf-8 -*-
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
