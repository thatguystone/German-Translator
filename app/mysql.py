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
			host = config.get("deutsch", "database.host"),
			user = config.get("deutsch", "database.user"),
			passwd = config.get("deutsch", "database.pass"),
			db = config.get("deutsch", "database.db"),
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
	
	def query(self, sql, args = ()):
		"""Runs a query against the database"""
		cn = MySQLdb.cursors.DictCursor(self.__db)
		
		suc = cn.execute(sql, args)
		
		if (self.__db.insert_id() != 0 and suc):
			ret = self.__db.insert_id()
		elif (not suc):
			ret = False
		else:
			ret = cn.fetchall()
			
			if (len(ret) == 0):
				ret = False
			elif (len(ret) == 1 and ret[0]["1"] == 1L): #special case for if we do a SELECT 1 FROM ... statement
				ret = True
		
		cn.close()
		return ret
