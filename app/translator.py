from config import config
import word
import utf8

def translate(query):
	"""Does the hefty work of translating the input"""
	
	query = utf8.encode(query)
	
	if (sentenceFigurer.canTranslate(query)):
		s = sentenceFigurer(query)
		return s.translate()
	else:
		w = word.word(query)
		return w.get()
	
class figurer(object):
	def __init__(self, query):
		self.query = query

class wordFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		return len(query.split(" ")) == 0
	
	def translate(self):
		#step 1: see if we have the word defined
		
		#step 2: no word was defined, attempt to break it down
		pass
		
class sentenceFigurer(figurer):
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		return len(query.split(" ")) > 1
	
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
			focus, index = self.__findFocus(words)
		else:
			#let's remove all the stars and start figuring out what we're looking at
			words = [word.word(w.replace("*", "")) for w in words]
			
			#let's remove the word we're focusing on
			focus = words[index]
			words.pop(index)
		
		#we can't do much for translating nouns, so just return their translations (and if it's compound,
		#it will be resolved via the lookup)
		if ((focus.isNoun() or focus.isAdjAdv()) and not focus.isVerb()):
			ret = focus.get()
		else: #it's a verb
			ret = self.__figureVerb(focus, words)
			
		return ret
	
	def __findFocus(self, words):
		pass
	
	def __figureVerb(self, verb, words):
		"""Attempts to figure out the tense (and the translation) for the given verb"""
		
		#first, let's scan the clause for other verbs to give us an idea of what we're looking at
		helpers = [v for v in words if v.isVerb()]
		
		if (len(helpers) > 0):
			return self.__figureVerbHelpers(verb, words)
		else:
			return self.__figureVerbWithoutHelper(verb, words)
	
	def __figureVerbHelpers(self, verb, words):
		helpers = [w for w in words if w.isHelper()]
		
		if (len(helpers) == 0):
			return () #well, we're looking at a verb with a helper but we didn't find any helpers....
		elif (len(helpers) == 1):
			#we only have 1 helper, let's just hit all the cases
			return self.__verbWithSingleHelper(helpers[0], verb)
	
	def __verbWithSingleHelper(self, helper, verb):
		ret = []
		
		#it's a helper, so we're safe grabbing its helper
		helperConj = helper.verb.getStem()
		helper = helper.verb.get(unknownHelper = True)[0]
		
		#if we're going for simple tenses
		if (helper["stem"] == "hab" or helper["stem"] == "sein"):
			#it's possible that we have numerous verbs that take the same past-tense form
			verbForms = []
			stem = verb.verb.getStem()
			
			#is the verb in the right form for having a helper?
			#check here to make sure that the entered verb is in the right past-tense form
			for v in verb.verb.get(helper["full"]):
				if (v["perfect"] == stem):
					verbForms.append(v)
			
			#two loops...otherwise things get far too indented and painful
			for verbForm in verbForms:
				#get the translation 
				trans = word.word(verbForm["full"]).get("verb")
				
				#process the translation into its proper output form
				if (helperConj == helper["third"] or helperConj == helper["stem"]):
					self.meaning(ret, "(past perfect)", trans, verbForm["full"])
				elif (helperConj == helper["subj2"]):
					self.meaning(ret, "(Konj.2 in past)", trans, verbForm["full"])
			
		#something going on with werden -> conditional present, passive voice
		elif (helper["stem"] == "werd"):
			#all the possible verbs (ex: gedenken + denken for gedacht)
			verbs = verb.verb.get(returnAll = True)
			
			enteredVerb = verb.getWord()
			
			#used for finding the correct conjugation
			enteredVerbStem = verb.verb.getStem()
			
			#####
			## Is there a better way to do this?
			#####
			
			#for each helper returned
			for k, h in verbs.iteritems():
				#for each verb
				for v in h:
					#get the translation
					trans = word.word(v["full"]).get("verb")
					
					#if we're looking at an unconjugated form of the verb: sehen
					if (enteredVerbStem == v["stem"]):
						#if: würde
						if (helperConj == helper["subj2"]):
							self.meaning(ret, "(fut./pres. conditional)", trans, v["full"])
						
						#if: wird
						elif (helperConj in (helper["third"], helper["stem"])):
							self.meaning(ret, "(future)", trans, v["full"])
					
					#the stem has been conjugated to past tense: gesehen
					elif (enteredVerbStem == v["perfect"]):
						
						#if: wurde
						if (helperConj == helper["preterite"]):
							self.meaning(ret, "(past passive)", trans, v["full"])
						
						#if: wird
						elif (helperConj in (helper["third"], helper["stem"])):
							self.meaning(ret, "(present passive)", trans, v["full"])
		
		return ret
		
	def __figureVerbWithoutHelper(self, verb, words):
		#we don't have a helper, so let's see what form our verb is taking
		stem = verb.verb.getStem()
		forms = verb.verb.get(unknownHelper = True)
		ret = []
		
		for form in forms:
			#run to our word translator -- grab all the verbs that match the infinitive
			trans = word.word(form["full"]).get("verb")
			
			#get the full form of the german verb that will be displayed
			verb = form["full"]
			
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
	
	def meaning(self, retList, tense, en, de):
		for t in en:
			retList.append(dict({"en": tense + " " + t["en"], "de": de}))
