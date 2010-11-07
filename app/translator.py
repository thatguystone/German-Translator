# -*- coding: utf-8 -*-
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
		#combine dashed-words into one word for easier access
		rawWords = self.query.replace("-", "").split(" ")
		numWords = len(rawWords)
		words = [word.word(w, i, numWords) for w, i in zip(rawWords, range(0, numWords))]
		
		#let's do a quick check to see if we have a separable prefix at the end of the sentence
		prefix = None
		if (words[len(words) - 1].isSeparablePrefix()):
			prefix = words[len(words) - 1]
			words.remove(prefix)
		
		#let's see
		focus, words = self.__findFocus(words, prefix)
		
		if (focus == None):
			return ()
		
		#we can't do much for translating nouns, so just return their translations (and if it's compound,
		#it will be resolved via the lookup)
		if ((focus.isNoun() or focus.isAdjAdv()) and not focus.isVerb()):
			return focus.get()
		else: #it's a verb
			return self.__figureVerb(focus, words)
	
	def __findFocus(self, words, prefix):
		"""
		Goes through all the words in the sentence and picks out the verbs (and adds on the prefix
		(if it exists) to the first verb found).  If no verbs are found (besides helpers), then we
		assume the helpers are being used as regular verbs, and we return those as a special case.
		Otherwise, we go through and attempt to find verb combinations (ie. `kennen lernen`), and
		return what we find, the first major verb found being the focus.
		"""
		
		#special cases -- for none or 1 found
		if (len(words) == 0):
			return (None, ())
		if (len(words) == 1):
			return (word.word(words[0]), ())
			
		#first, let's attempt to find a verb that's not a helper
		verbs = [w for w in words if w.isVerb() and not w.isHelper()]
		
		#if there are other verbs in the sentence that are not helpers
		if (len(verbs) > 0):
			#if we're add a prefix (and thus skipping verb combining)
			if (prefix != None):
				#the prefix always combines with the first word in the sentence
				verb = verbs[0]
				focus = word.word(prefix.word + verb.word, verb.loc, verb.numWords)
				
				#should we ignore the prefix because it does nothing?
				if (focus.isVerb()):
					words.remove(verb)
				else:
					focus = verb
			else: #we're going for verb combining, just to make sure
				#if we found some verbs, let's pick out the main one in the sentence
				focus, rmWords = self.__combineVerbs(verbs)
				
				#if we have something, then go ahead and clear it from our search entries
				if (len(rmWords) > 0):
					for w in rmWords:
						words.remove(w)
			
			return (focus, words)
		else: #we only have helper verbs
			verbs = [w for w in words if w.isVerb()]
			
			#it's possible we don't have any verbs...which is an ERROR
			if (len(verbs) == 0):
				return (None, ())
			elif (len(verbs) == 1):
				#if our helper has a prefix (ie. `anhaben`)
				if (prefix != None):
					verb = verbs[0]
					sepVerb = word.word(prefix.word + verb.word, verb.loc, verb.numWords)
					
					#make sure our separable verb is actually a verb
					if (sepVerb.isVerb()):
						return (sepVerb, ())
						
					return (verb, ())
				else:
					#no prefix on the helper, he's just himself. Cool.
					return (verbs[0], ())
			else:
				#there are numerous helpers, just use the last as the focus
				return (verbs[len(verbs) - 1], verbs[:len(verbs) - 1])
			
	def __combineVerbs(self, verbs):
		if (len(verbs) == 1):
			#if we only have one verb, this is a special case...
			focus = verbs[0] #get our focus verb
			return (focus, [focus])
		
		#attempt to combine the verbs in some meaningful way to see if we find anything
		#ex: kennen lernen, scheiden lassen, schneiden lassen
		for i in verbs:
			for j in verbs:
				#if we're comparing a word to itself...well, that won't work
				if (i == j):
					continue
					
				tmpWord = word.word(i.word + " " + j.word)
				#if we didn't find a word (because it just doesn't exist)
				if (not tmpWord.exists()):
					continue
				
				#oh hey, if we get here, we're definitely looking at a verb combination! yay!
				return (tmpWord, (i, j))
		
		return (None, [])
	
	def __figureVerb(self, verb, words):
		"""Attempts to figure out the tense (and the translation) for the given verb"""
		
		#first, let's scan the clause for other verbs to give us an idea of what we're looking at
		helpers = [v for v in words if v.isVerb()]
		
		if (len(helpers) == 0):
			return self.__verbWithoutHelper(verb, words)
		elif (len(helpers) == 1):
			return self.__verbWithSingleHelper(helpers[0], verb)
		else:
			return self.__multipleVerbs(helpers, verb)
	
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
				if (helperConj in (helper["third"], helper["first"], helper["stem"])):
					self.meaning(ret, "(past perfect)", trans, verbForm["full"])
				elif (helperConj == helper["subj2"]):
					self.meaning(ret, "(Konj.2 in past)", trans, verbForm["full"])
				elif (helperConj == helper["preterite"]):
					self.meaning(ret, "(Plusquamperfekt)", trans, verbForm["full"])
			
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
						elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
							self.meaning(ret, "(future)", trans, v["full"])
					
					#the stem has been conjugated to past tense: gesehen
					elif (enteredVerbStem == v["perfect"]):
						
						#if: wurde
						if (helperConj == helper["preterite"]):
							self.meaning(ret, "(past passive)", trans, v["full"])
						
						#if: wird
						elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
							self.meaning(ret, "(present passive)", trans, v["full"])
		
		return ret
		
	def __verbWithoutHelper(self, verb, words):
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
			elif (stem in (form["third"], form["first"], form["stem"])):
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
