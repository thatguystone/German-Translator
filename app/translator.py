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
		if ((focus.isNoun() or focus.isAdjAdv()) and not focus.isVerb()):
			ret = focus.get()
		else: #it's a verb
			verb = data.canoo(focus.getWord())
			if (verb.exists()):
				ret = self.__beVerby(words, verb)
			else:
				ret = ()
			
		return ret
	
	def __beVerby(self, words, verb):
		"""
		As the name applies, this makes the verb more verby, in that we try to figure out what the
		verb is functioning as in the sentence
		"""
		
		#first, let's scan the clause for other verbs to give us an idea of what we're looking at
		helpers = [v.getVerb() for v in words if v.isVerb()]
		
		#if we have helpers, then we have to do a little more work
		if (len(helpers) > 0):
			return self.__helperVerby(verb, helpers, words)
		else:
			#we don't have a helper, so let's see what form our verb is taking
			stem = verb.getVerb().getStem()
			forms = verb.get(unknownHelper = True)
			verb = verb.getVerb().getString()
			
			ret = []
			
			for form in forms:
				#run to our word translator -- grab all the verbs that match the infinitive
				trans = data.lookup(unicode(form["full"])).get("verb")
				
				#let's take a look at our forms and see what we can find
				if (form["preterite"] == stem):
					self.meaning(ret, "(simple past)", trans, verb)
				elif (form["third"] == stem or form["stem"] == stem):
					#this might seem a bit weird -- we need to compare our stem to the stem from the site to see if it's present tense
					#we also use third because that one might conjugate differently, but it's still present tense
					self.meaning(ret, "(present)", trans, verb)
				elif (form["subj2"] == stem):
					self.meaning(ret, "(conditional)", trans, verb)
				else:
					pass #not sure what we're looking at, but it's not correct
			
			return ret
		
	def __helperVerby(self, verb, helpers, words):
		"""
		Goes through the list of words and attempts to find what the helper verbs are doing to the verb
		"""
		
		#attempt to find what this helper is doing
		helper = helpers[0].get(unknownHelper = True)
		helperStem = helpers[0].getVerb().getStem()
		
		#right now, we only handle sentences with 2 verbs
		
		#only do something if we could find the helper
		if (len(helper) > 0):
			helper = helper[0]
			
			ret = []
			
			if (helper["stem"] == "hab" or helper["stem"] == "sei"):
				#process the past tense with a helper verb
				
				#it's possible that we have numerous verbs that take the same past-tense form
				verbForms = []
				stem = verb.getVerb().getStem()
				
				for v in verb.get(helper["full"]):
					#is the verb in the right form for having a helper?
					if (v["perfect"] == stem):
						verbForms.append(v)
				
				#two loops...otherwise things get far too indented and painful
				for verbForm in verbForms:
					#get the translation 
					trans = data.lookup(unicode(verbForm["full"])).get("verb")
					
					#process the translation into its proper output form
					if (helperStem == helper["third"] or helperStem == helper["stem"]):
						self.meaning(ret, "(past perfect)", trans, unicode(verbForm["full"]))
					elif (helperStem == helper["subj2"]):
						self.meaning(ret, "(Konj.2 in past)", trans, unicode(verbForm["full"]))
				
				return ret
			elif (helper["stem"] == "werd"):
				#something going on with werden -> conditional present, passive voice
				enteredVerbStem = unicode(verb.getVerb().getStem())
				enteredVerb = unicode(verb.getVerb())
				verbs = verb.get(returnAll = True)
				
				#the conjugated form of the helper
				helperConj = unicode(helpers[0].getVerb().getStem())
				
				for k, h in verbs.iteritems(): #for each helper returned
					for v in h: #for each verb
						trans = data.lookup(unicode(v['full'])).get("verb")
					
						if (helperConj == helper["subj2"]):
							#conditional (present/future)
							if (enteredVerb == v["full"]):
								self.meaning(ret, "(fut./pres. conditional)", trans, enteredVerb)
						elif (helperConj == helper["stem"] or helperConj == helper["third"]):
							#future
							if (enteredVerb == v["full"]):
								self.meaning(ret, "(future)", trans, enteredVerb)
						elif (helperConj == helper["preterite"]):
							#passive
							if (enteredVerbStem == v["perfect"]):
								self.meaning(ret, "(passive)", trans, enteredVerb)
				
		#we couldn't even find the helper...that's discouraging
		return ret
		
	def meaning(self, retList, tense, en, de):
		for t in en:
			retList.append(dict({"en": tense + " " + t["en"], "de": de}))
		
class wordFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		#more or less, compounds are going to be more than 6 letters
		return (len(query) > 6)
	
	def translate(self):
		print "word"
