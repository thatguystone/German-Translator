import data

class cacher(data.data):
	"""Controls the cache of words that we have already solved"""
	
	def exists(self, word):
		return False
	
	def get(self, word):
		return self.db.query("SELECT * FROM `test`")
