#
# Copyright (c) 2010 Andrew Stone
#
# Copyright (c) 2010 Andrew Stone
#
# This file is part of of of Verbinator.
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
def encode(s):
	ret = s
	if (type(s) != unicode):
		ret = unicode(s, "utf-8")
	
	return ret
