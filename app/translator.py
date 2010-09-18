from config import config
import data

#what we are attempting to translate
query = ""

def setQuery(q):
	"""Sets what we are attempting to figure out -- call this before calling the other functions"""
	
	global query
	query = q

def canTranslate():
	"""A basic check to see if we actually know how to translate the query"""
	
	return config.getboolean("deutsch", "enable.translator") and (sentenceFigurer.canTranslate(query) or wordFigurer.canTranslate(query))

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
		
		return (query.find("*") > 0 and len(query.split(" ")) > 1)
	
	def translate(self):
		"""Assumes we can translate it, then runs a sentence guesser on it"""
		
		#start off by getting the different words in the sentence
		words = self.query.replace("-", "").split(" ") #combine dashed-words into one word for easier access
		
		#let's find which word they're asking about
		for w, i in zip(words, range(len(words))):
			if (w.find("*") >= 0):
				index = i
				break
		
		#if we didn't find a word to figure out
		if (not "index" in locals()):
			print "\nError: No word for translation was specified\n"
			return ()
		
		#let's remove all the stars and start figuring out what we're looking at
		words = [data.lookup(w.replace("*", "")) for w in words]
		
		#we can't do much for translating
		#adjectives/adverbs/nouns (if it's a compound in a sentence, it will be recursively resolved
		#through lookup), so just return their translations
		if (words[index].isAdjAdv() or words[index].isNoun()): 
			ret = words[index].get()
		else:
			print "here"
			
		return ret

class wordFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		#more or less, compounds are going to be more than 6 letters
		return (len(query) > 6)
	
	def translate(self):
		print "word"
