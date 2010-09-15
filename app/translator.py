#what we are attempting to translate
query = ""

def setQuery(q):
	"""Sets what we are attempting to figure out -- call this before calling the other functions"""
	
	global query
	query = q

def canTranslate():
	"""A basic check to see if we actually know how to translate the query"""
	
	return sentenceFigurer.canTranslate(query) or wordFigurer.canTranslate(query)

def translate():
	"""Does the actual translation"""
	
	if (sentenceFigurer.canTranslate(query)):
		trn = sentenceFigurer(query)
	else:
		trn = wordFigurer(query)
	
	return trn.translate()

class figurer(object):
	def __init__(self, query):
		self.query = query

class sentenceFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		return (len(query.split(" ")) > 1)
	
	def translate(self):
		print "sentence"

class wordFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		#more or less, compounds are going to be more than 6 letters
		return (len(query) > 6)
	
	def translate(self):
		print "word"
