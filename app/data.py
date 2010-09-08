from mysql import mysql

class data:
	def __init__(self):
		self.db = mysql.getInstance()
