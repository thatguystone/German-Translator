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
		
		#let's remove the word we're focusing on
		focus = words[index]
		words.pop(index)
		
		#we can't do much for translating nouns, so just return their translations (and if it's compound,
		#it will be resolved via the lookup)
		if (1 == 2 and focus.isNoun()): 
			ret = focus.get()
		else:
			verb = data.canoo(focus.getWord())
			word = verb.get()
			
			#if it's an adj/adv, it might be a verb, so let's run a check on that.
			isAdv = focus.isAdjAdv()
			isVerb = focus.isVerb()
				
			ret = ()
			
		return ret

class wordFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		#more or less, compounds are going to be more than 6 letters
		return (len(query) > 6)
	
	def translate(self):
		print "word"
