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
	
class sentenceFigurer(object):
	def __init__(self, query):
		self.query = query
	
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
		
		self.__doPrefix(words)
		
		#do the verbs
		meanings, usedVerbs = self.__goForTheVerbs(words[:]) #don't let him mutilate my word list!
		
		#check for the participles, and append them to our translations
		[meanings.append(p) for p in self.__goForParticiples(words, usedVerbs)]
		
		return meanings
	
	def __doPrefix(self, words):
		#let's do a quick check to see if we have a separable prefix at the end of the sentence
		prefix = None
		if (words[len(words) - 1].isSeparablePrefix()):
			prefix = words[len(words) - 1]
			words.remove(prefix)
			
			#and attach the prefix to the first verb in the sentence
			for w, i in zip(words, range(0, len(words))):
				if (w.isVerb()):
					words[i] = word.word(prefix.word + w.word, w.loc, w.numWords)
					break
	
	"""
	************************************************************************************************
	*** Functions that work on verbs as adjectives (participles)
	"""
	
	def __goForParticiples(self, words, usedVerbs):
		#our list of participles and their meanings
		ret = []
		
		#let's just run through the sentence, again, and see what we find
		#be sure we only use verbs we found that haven't been used as verbs yet
		for w in [w for w in words if w not in usedVerbs]:
			if w.isParticiple():
				stem, form = w.verb.getParticipleStem()
				
				if (stem == form["perfect"]):
					tense = "past participle"
				else:
					tense = "present participle"
				
				self.meaning(ret, tense, word.word(form["full"]).get("verb"), form["full"], w)
		
		return ret
	
	"""
	************************************************************************************************
	*** Functions that work on figuring out verb tenses
	"""
	
	def __goForTheVerbs(self, words):
		"""Picks the verbs out of the sentence and does stuff with them."""
		#let's see
		focus, words = self.__findFocus(words)
		
		if (focus == None):
			return ([], [])
		
		#we can't do much for translating nouns, so just return their translations (and if it's compound,
		#it will be resolved via the lookup)
		if ((focus.isNoun() or focus.isAdjAdv()) and not focus.isVerb()):
			return focus.get()
		else: #it's a verb
			return self.__figureVerb(focus, words)
	
	def __figureVerb(self, verb, words):
		"""Attempts to figure out the tense (and the translation) for the given verb"""
		
		#first, let's scan the clause for other verbs to give us an idea of what we're looking at
		helpers = [v for v in words if v.isVerb()]
		
		if (len(helpers) == 0):
			meanings = self.__verbWithoutHelper(verb, words)
			usedVerbs = [verb]
		elif (len(helpers) == 1):
			meanings = self.__verbWithSingleHelper(helpers[0], verb)
			
			#if we found meanings (ie. we had "ich habe geglaubt", not "ich bin geglaubt")
			if (len(meanings) > 0):
				usedVerbs = [helpers[0], verb]
			else:
				#there were no meanings, so attempt it as though the verb is a predicate adjective
				meanings = self.__verbWithoutHelper(helpers[0], words)
				#if we still found nothing
				if (len(meanings) == 0):
					usedVerbs = []
				else:
					usedVerbs = [helpers[0]]
					
		else:
			meanings = []
			usedVerbs = []
			#not implemented yet
			#meanings = self.__multipleVerbs(helpers, verb)
			pass
		
		return (meanings, usedVerbs)
	
	def __findFocus(self, words):
		"""
		Goes through all the words in the sentence and picks out the verbs (and adds on the prefix
		(if it exists) to the first verb found).  If no verbs are found (besides helpers), then we
		assume the helpers are being used as regular verbs, and we return those as a special case.
		Otherwise, we go through and attempt to find verb combinations (ie. `kennen lernen`), and
		return what we find, the first major verb found being the focus.
		"""
		
		#special cases -- for none or 1 found
		if (len(words) == 0):
			return (None, [])
		if (len(words) == 1):
			return (word.word(words[0]), [])
			
		#first, let's attempt to find a verb that's not a helper
		verbs = [w for w in words if w.isVerb() and not w.isHelper()]
		
		#if there are other verbs in the sentence that are not helpers
		if (len(verbs) > 0):
			#if we found some verbs, let's pick out the main one in the sentence
			focus, rmWords = self.__combineVerbs(verbs)
			
			#if we didn't get anything from combining
			if (focus == None):
				#then our focus is the last word
				rmWords = verbs
				focus = rmWords[len(verbs) - 1]
			
			#if we have something, then go ahead and clear it from our search entries
			if (len(rmWords) > 0):
				for w in rmWords:
					words.remove(w)
		
			return (focus, words)
		else: #we only have helper verbs
			verbs = [w for w in words if w.isVerb()]
			
			#it's possible we don't have any verbs...which is an ERROR
			if (len(verbs) == 0):
				return (None, [])
			elif (len(verbs) == 1):
				#no prefix on the helper, he's just himself. Cool.
				return (verbs[0], [])
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
				
				if (not (i.exists() and j.exists())):
					continue
				
				tmpWord = word.word(i.verb.get(True)[0]["full"] + " " + j.verb.get(True)[0]["full"])
				#if we didn't find a word (because it just doesn't exist)
				if (not tmpWord.exists()):
					continue
				
				#oh hey, if we get here, we're definitely looking at a verb combination! yay!
				return (tmpWord, (i, j))
		
		return (None, [])
	
	def __verbWithSingleHelper(self, helper, verb):
		ret = []
		
		#it's a helper, so we're safe grabbing its helper
		helperConj = helper.verb.getStem()
		helper = helper.verb.get(unknownHelper = True)[0]
		
		#if we're going for simple tenses
		if (helper["stem"] == "hab" or helper["stem"] == "sein"):
			#it's possible that we have numerous verbs that take the same past-tense form
			verbs = []
			stem = verb.verb.getStem()
			
			#if we have a verb like "kennen lernen" and we have the right helper verb
			if (verb.verb.word != verb.word and helper["full"] == verb.verb.get(True)[0]["hilfsverb"]):
				verbs.append((verb, verb.verb.get(True)[0]))
			else:
				#is the verb in the right form for having a helper?
				#check here to make sure that the entered verb is in the right past-tense form
				for v in verb.verb.get(helper["full"]):
					#make sure we have the right helper, too
					if (v["perfect"] == stem and v["hilfsverb"] == helper["full"]):
						verbs.append((word.word(v["full"], verb.loc, verb.numWords), v))
			
			#two loops...otherwise things get far too indented and painful
			for v, verbForm in verbs:
				#get the translation 
				trans = v.get("verb")
				
				#process the translation into its proper output form
				if (helperConj in (helper["third"], helper["first"], helper["stem"])):
					self.meaning(ret, "past perfect", trans, v.word, v)
				elif (helperConj == helper["subj2"]):
					self.meaning(ret, "Konj.2 in past", trans, v.word, v)
				elif (helperConj == helper["preterite"]):
					self.meaning(ret, "Plusquamperfekt", trans, v.word, v)
			
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
							self.meaning(ret, "fut./pres. conditional", trans, v["full"], verb)
						
						#if: wird
						elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
							self.meaning(ret, "future", trans, v["full"], verb)
					
					#the stem has been conjugated to past tense: gesehen
					elif (enteredVerbStem == v["perfect"]):
						
						#if: wurde
						if (helperConj == helper["preterite"]):
							self.meaning(ret, "past passive", trans, v["full"], verb)
						
						#if: wird
						elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
							self.meaning(ret, "present passive", trans, v["full"], verb)
		
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
			verbForm = form["full"]
			
			#let's take a look at our forms and see what we can find
			if (form["preterite"] == stem):
				self.meaning(ret, "simple past", trans, verbForm, verb)
			elif (stem in (form["third"], form["first"], form["stem"])):
				#this might seem a bit weird -- we need to compare our stem to the stem from the site to see if it's present tense
				#we also use third because that one might conjugate differently, but it's still present tense
				self.meaning(ret, "present", trans, verbForm, verb)
			elif (form["subj2"] == stem):
				self.meaning(ret, "conditional", trans, verbForm, verb)
			else:
				pass #not sure what we're looking at, but it's not correct
		
		return ret
	
	def meaning(self, retList, tense, en, dePrintable, deVerb):
		"""
		Puts the translations into the output dictionary list.
		dePrintable -- the german word that should be displayed in the translation table.
		deVerb -- the word.word for the translation
		"""
		
		for t in en:
			retList.append(dict({
				"en": "(" + tense + ") " + t["en"],
				"de": dePrintable,
				"deOrig": deVerb.word,
				"deWordLocation": deVerb.loc
			}))
