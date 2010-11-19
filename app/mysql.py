import MySQLdb
from config import config

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
		self.__db = MySQLdb.connect(
			host = config.get("deutsch", "database.host", raw=True),
			user = config.get("deutsch", "database.user", raw=True),
			passwd = config.get("deutsch", "database.pass", raw=True),
			db = config.get("deutsch", "database.db", raw=True),
			charset = "utf8",
			use_unicode = True
		)

		#since we're going to be using special characters, go directly to UTF-8
		self.__db.set_character_set('utf8')
		self.query('SET NAMES utf8;')
		self.query('SET CHARACTER SET utf8;')
		self.query('SET character_set_connection=utf8;')
		
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
		cn = MySQLdb.cursors.DictCursor(self.__db)
		
		suc = cn.execute(sql, args)
		
		if (not suc):
			ret = False
		else:
			ret = cn.fetchall()
			
			if (len(ret) == 0):
				ret = False
			elif (len(ret) == 1 and (("1" in ret[0].keys()) and ret[0]["1"] == 1L)): #special case for if we do a SELECT 1 FROM ... statement
				ret = True
		
		cn.close()
		return ret
