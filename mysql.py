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
import bottle
import pymysql

app = bottle.default_app()

class mysql(object):
	"""
	This class has roughly been adapted from its counterpart in PHP.  Rather than having a rigid,
	hard-to-use interface to the database, this defines a nice abstraction away from it that merely
	executes queries and returns usable results (in dictionary form).
	"""

	#a class variable for holding the instance of self
	__instance = None

	#an instance variable, holds the db connection
	__db = None

	def __init__(self):
		self.__db = pymysql.connect(
			host = app.config['database.host'],
			user = app.config['database.user'],
			passwd = app.config['database.pass'],
			db = app.config['database.db'],
			charset = "utf8",
			use_unicode = True
		)

		#since we're going to be using special characters, go directly to UTF-8
		self.query('SET NAMES utf8;')
		self.query('SET CHARACTER SET utf8;')
		self.query('SET character_set_connection=utf8;')

	def close(self):
		self.__db.close()
		mysql.__instance = None

	@classmethod
	def getInstance(cls):
		if (type(cls.__instance) != mysql):
			cls.__instance = mysql()

		return cls.__instance

	def insert(self, sql, args = ()):
		"""Special method for insert statements only.

		There is a bug that causes the mysql driver for python to return a number for
		conn.insert_id() after an insert has been done.  To avoid returning
		the last insert id for every row queried after an insert, I broke it off into its
		own function."""

		res = self.query(sql, args)
		self.__db.commit()

		if (self.__db.insert_id() != 0 and bool(res)):
			ret = self.__db.insert_id()
		else:
			ret = False

		return ret

	def query(self, sql, args = ()):
		"""Runs a query against the database"""
		cur = self.__db.cursor(pymysql.cursors.DictCursor)
		suc = cur.execute(sql, args)

		if (not suc):
			ret = False
		else:
			ret = cur.fetchall()

			if not ret:
				ret = False
			elif (len(ret) == 1 and (("1" in ret[0].keys()) and ret[0]["1"] == 1L)): #special case for if we do a SELECT 1 FROM ... statement
				ret = True

		cur.close()
		return ret
