# -*- coding: utf-8 -*-
import re

from config import config
import word
import utf8

def translate(query):
	"""Does the hefty work of translating the input"""

	query = utf8.encode(query)
	
	#replace ae, oe, ue with ä, ö, ü
	for i in (("ae", u"ä"), ("oe", u"ö"), ("ue", u"ü")):
		query = query.replace(i[0], i[1])
	
	if (sentenceFigurer.canTranslate(query)):
		s = sentenceFigurer(query)
		return s.translate()
	else:
		w = word.word(query)
		return w.get()

def printWords(words):
	print [w.word for w in words]

class sentenceFigurer(object):
	def __init__(self, query):
		while (query.find("  ") > -1):
			query = query.replace("  ", " ")
		
		self.query = query.strip()
	
	@classmethod
	def canTranslate(cls, query):
		"""A basic checker to see if it's even worthwhile running this on the query"""
		
		return len(query.split(" ")) > 1
	
	def translate(self):
		"""Assumes we can translate it, then runs a sentence guesser on it"""
		
		query = re.sub("[\(\)\-\&\$\%\#\@\[\]\{\}\+\=\"\']*", "", self.query)
		
		tmpClauses = [r.strip() for r in re.split("[,\.\?\!\;]*", query) if len(r) > 0]
		
		#do a pass over the sentence to count words and stuff and stuff
		words = []
		numWords = 0
		for c in tmpClauses:
			w = c.split(" ")
			numWords += len(w)
			words.append(w)
		
		#and now do a final pass to build up our word objects
		loc = 0
		ret = []
		for w in words:
			wLen = len(w)
			w = [word.word(w, loc + i, i, wLen) for w, i in zip(w, range(0, wLen))]
			ret += clauseFigurer().translate(w)
			loc += wLen
		
		return ret

class clauseFigurer(object):
	def translate(self, words):
		"""Given a complete clause, finds relations amongst verbs and determines their tenses."""
		
		#run for all the possible verbs (participles could be included in this list)
		tmpVerbs = [v for v in words if v.isVerb()]
		
		if (len(tmpVerbs) == 0):
			return []
		
		#all the possible verbs in the sentence
		possibleVerbs = [v for v in tmpVerbs if not v.verb.isPresentParticiple()]
		
		#the present participles that were originally mistaken for verbs -- they were excluded in
		#the above statement, so we need to grab them here
		participles = [v for v in tmpVerbs if v not in possibleVerbs]
		
		#only add in past participles if they're not in our list of possible verbs -- if it is really
		#a participle and included in the list of possible verbs, it will be pruned out later
		[participles.append(w) for w in words if w not in possibleVerbs and w.verb.isPastParticiple()]
		
		#present particples are easy -> only add them if they were not gotten from the mistaken list of
		#verbs above
		[participles.append(w) for w in words if w not in participles and w.verb.isPresentParticiple()]
		
		#step 2: since we are in a clause, we have isolation from all other verbs, so let's
		#start building out our verb tree
		#
		#do we have a separable prefix that needs re-attaching?
		lastWord = words[len(words) - 1]
		if (lastWord.isSeparablePrefix()):
			#attempt to see if when we add the prefix to the verb, it is still a verb
			prefixed = word.word(lastWord.word + possibleVerbs[0].word, possibleVerbs[0].sentLoc, possibleVerbs[0].clauseLoc, possibleVerbs[0].numWords)
			if (prefixed.isVerb()):
				tmpVerbs.remove(possibleVerbs[0])
				possibleVerbs[0] = prefixed #it's a separable verb, so replace it
		
		#pass it onto the tree constructor to build out our verb tree
		tree = verbTree(possibleVerbs)
		tree.build()
		
		#do our first pass on the tree to clean out the remaining participles
		tree.translate(translate = False)
		
		#add the mistaken participles to our participle list
		participles += tree.pruneParticiples()
		
		#do a second pass (now that it's clean) for the actual tenses and translations
		tree.translate(translate = True)

		#debugging dump of the tenses and nodes
		if (config.getboolean("deutsch", "debug")):
			tree.dump()
		
		#grab all the used verbs
		verbs = tmpVerbs[:]
		[verbs.remove(v) for v in tree.getVerbs() if v in verbs]
		
		#only add participles to our list if they're not already in the list (no duplicates allowed)
		#anything left over in verbs as this point was not used in the tree, so chances are it is
		#a participle
		[participles.append(v) for v in verbs if v not in participles]
		
		#the meanings of the used, conjugated verbs
		meanings = tree.getMeanings()
		self.__participleMeanings(participles, meanings)
		return meanings
	
	def __participleMeanings(self, participles, meanings):
		#add our participles to our meanings
		for p in participles:
			presentParticiple = p.verb.isPresentParticiple()
			forms = p.verb.get(unknownHelper = True)
			
			#save the full form of our word for the translation
			origWord = p.verb.word
			
			#if we found no conjugations for the verb, then we had something like "gesehenen",
			#so we need to get a new word from the stem of the participle, then we let the
			#translator run through all its stuff and get the meaning of the verb, and then to
			#the output it goes
			if (len(forms) == 0):
				p = word.word(p.verb.getParticipleStem()[0], p.sentLoc, p.clauseLoc, p.numWords)
				forms = p.verb.get(True)
				
			fullForm = forms[0]["full"]
			loc = p.sentLoc
			
			#fix for python 2.4
			tense = "past participle"
			if (fullForm == origWord):
				tense = "infinitive" 
			elif (presentParticiple):
				tense = "present participle"
			
			for t in p.get("verb"):
				meanings.append({
					"en": "(" + tense + ") " + t["en"],
					"de": fullForm,
					"deOrig": origWord,
					"deWordLocation": loc
				})

class tenses(object):
	CONDITIONAL = "konj.2 in fut./pres."
	CONDITIONAL_PAST = "konj.2 in past"
	FUTURE = "future"
	FUTURE2 = "future 2"
	INFINITIVE = "infinitive"
	PASSIVE_PAST = "past passive"
	PASSIVE_PRESENT = "present passive"
	PAST_PERFECT = "past perfect"
	PLUSQUAM = "plusquamperfekt"
	PRESENT = "present"
	PRETERITE = "preterite"

class verbTree(object):
	def __init__(self, verbs):
		self.verbs = verbs
		self.numVerbs = len(self.verbs)
		self.node = None
	
	def build(self):
		"""
		Starts the construction of the tree -- it finds the first verb that all verbs in the sentence
		attach to, then it passes off the remaining verbs (which MUST be at the end of the clause)
		to the node to figure out
		"""
		
		#we can never start off with a participle -> that's not even a verb!
		for i, v in zip(range(0, self.numVerbs), self.verbs):
			if (v.verb.isParticiple()):
				continue
			
			verb = i
			break
		
		#let's determine if we're in a nebensatz
		#if the verb we found is in the middle of the collection of verbs at the end of the sentence
		#or at the start of it, then we're looking at a nebensatz
		fromEnd = self.verbs[i].numWords - (self.verbs[i].clauseLoc + 1)
		
		#only look at it if our verb is towards the end and it's not just some short clause
		#with the verb in 1st or 2nd position, but that still happens to be near the end
		if ((fromEnd <= 3 and fromEnd >= 0) and self.verbs[i].clauseLoc >= 2):
			#we have a special case here: any helper in Konj2 form changes the form of the sentence
			#so let's just do a quick check to see if we're dealing with that before we resign
			#ourselves to a full-blown nebensatz
			verb = self.verbs[i]
			stem = verb.verb.getStem()
			form = verb.verb.get(True)[0]
			
			if (fromEnd != 0 and form["subj2"] == stem):
				self.node = verbNode(verb, self.verbs[i + 1:])
			
			#just to be sure -- check that the last word in the sentence is a helper or a modal
			#Note: this has no impact on `kennen lernen` verbs as they are combined with parent / child
			#on run, so their order doesn't really matter in nebensätze -> without a helper, they are
			#combined, and with a helper, the fall into the below if and they are still combined
			else:
				lastVerb = self.verbs[self.numVerbs - 1]
				if (lastVerb.verb.isModal() or lastVerb.verb.isHelper()):
					self.node = verbNode(lastVerb, self.verbs[:self.numVerbs - 1])
		
		#if we weren't in a nebensatz, process as normal
		if (self.node == None):
			self.node = verbNode(self.verbs[i], self.verbs[i + 1:])
		
		self.node.process()
		
	def translate(self, translate = False):
		"""
		Triggers translate on the tree.
		translate (bool) - If meanings should be looked up
		"""
		
		if (self.node == None):
			return
		
		verbNode.doTranslations = translate
		
		#and trigger the nodes to start giving their tenses back
		self.node.translate()
	
	def pruneParticiples(self):
		"""
		Once we translate a sentence, we can go through and remove any participles caught at the end
		of a clause that were mistaken for verbs.
		"""
		
		participles = []
		
		#instruct the tree to prune itself
		self.node.pruneParticiples(None, participles)
		
		return participles
	
	def getMeanings(self):
		meanings = []
		self.node.appendMeanings(meanings)
		return meanings
	
	def getVerbs(self):
		verbs = []
		self.node.appendVerbs(verbs)
		return verbs
	
	def dump(self):
		self.node.dump()
		print

class verbNode(object):
	doTranslations = False
	
	def __init__(self, verb, remainingVerbs):
		#the defineable form of the verb
		self.verb = verb

		#the remaining verbs that need put into the tree
		self.remaining = remainingVerbs
		self.lenRemain = len(remainingVerbs)
		
		#another reference to the verb -- if we have a verb like `kennen lernen`, then this will
		#be set to its infinitive form
		# * for example: if verb is "kennen gelernt", this will be "gelernt" as that is the conjugateable
		#   form of the verb
		self.conjugation = self.verb
		
		#we always have to have a child, even if nothing
		self.child = None
		
		#we start of not being combined with anything
		self.isCombined = False
		
		#and the translations for our verb
		self.meanings = []
		
		#for if we combine with a child
		self.verbs = None
		
		#the tense of our verb, none by default just for safe-keeping
		#Note: if everything in the tree doesn't have a tense set, then the sentence is not 
		# valid, so we couldn't determine any tenses
		self.tense = None
	
	def setTense(self, tense):
		self.tense = tense
	
	def process(self):
		"""
		Goes through the remaining verbs, from the back->front (this is how they now take precedence),
		and attempts to attach them to each other.
		"""
		
		#we're at the bottom of the tree
		if (self.lenRemain == 0):
			return
		
		#take a look at the next verb to process
		next = self.remaining[self.lenRemain - 1]
		
		self.child = verbNode(next, self.remaining[:self.lenRemain - 1])
		self.child.process()
		
		#let's see if we can somehow combine with our child (for `kennen lernen` verbs)
		if (self.child != None and not self.child.isCombined):
			self.combineWithChild()
	
	def pruneParticiples(self, parent, participles):
		#if we don't have a tense AND we're a past-participle, then we're clearly out of place
		#all of the present ones were removed from the tree (those were easy), now we know
		#(after the parse) what we definitely are
		if (self.tense == None and self.verb.verb.isPastParticiple()):
			participles.append(self.verb)
			
			if (parent != None):
				#make the parent bypass us -- we're not a verb, so we can't do anything
				parent.child = self.child
			
			if (self.child != None):
				#continue on with our child, but bypass us completely and just pass the new parent
				#as his parent
				self.child.pruneParticiples(parent, participles)
		
		#we don't qualify, move on to our child
		elif (self.child != None):
			#if we have an infinitive as our child without at ense, and we don't have a tense, lose it
			#it's an infinitive, and we have no use for it
			if (self.tense == None
				and
				self.child.tense == None
				and
				self.child.verb.verb.word == self.child.verb.verb.get(True)[0]["full"]
			):
				participles.append(self.child.verb)
				self.child = None
			else:
				self.child.pruneParticiples(self, participles)
	
	def appendMeanings(self, meanings):
		[meanings.append(m) for m in self.meanings]
		if (self.child != None):
			self.child.appendMeanings(meanings)
	
	def appendVerbs(self, verbs):
		if (self.verbs != None):
			for v in self.verbs:
				verbs.append(v)
		else:
			verbs.append(self.verb)
		
		if (self.child != None):
			self.child.appendVerbs(verbs)
	
	def combineWithChild(self):
		#first, let's see if it's even legal for us to combine with one of our children
		if (self.verb.verb.isModal() or self.verb.verb.isHelper()):
			return
		
		#the first verb to compare
		first = self.child.verb
		firstFull = first.verb.get(True)[0]["full"]
		#and the second
		second = self.verb
		secondFull = second.verb.get(True)[0]["full"]
		
		forms = (
			(word.word(firstFull + " " + secondFull, first.sentLoc, first.clauseLoc, first.numWords), second),
			(word.word(secondFull + " " + firstFull, first.sentLoc, first.clauseLoc, first.numWords), first),
			(word.word(firstFull + secondFull, first.sentLoc, first.clauseLoc, first.numWords), second),
			(word.word(secondFull + firstFull, first.sentLoc, first.clauseLoc, first.numWords), first)
		)
		
		#go through all possible combinations
		for f in forms:
			if (len(f[0].translations.searchFromDB()) > 0):
				#store the conjugation and defineable forms
				self.verb = f[0]
				self.conjugation = f[1]
				
				#we're absorbing our child, remove him
				self.child = self.child.child
				
				#and store the verbs we used to return in appendVerbs()
				self.verbs = (first, second)
				
				#and set our flag that we're not combined with our child
				self.isCombined = True
				break
	
	def translate(self):
		if (self.verb.isHelper()):
			self.__translateAsHelper()
		elif (self.verb.verb.isModal()):
			self.__translateModal()
			if (self.child != None):
				self.child.translate()
		else:
			self.__standAlone()
	
	def __translateAsHelper(self):
		#if we have a child, then we are helping the child change his tense
		if (self.child != None):
			self.child.__translateWithParent(self)
		
		#otherwise, we're operating as our own verb, yayz!
		else:
			self.__standAlone()
	
	def __standAlone(self):
		#looks like we're just a verb by our lonesome in a big, bad sentence :(
		form = self.conjugation.verb.get(True)
		stem = self.conjugation.verb.getStem()
		self.__setNormalTenses(form, stem)
	
	def __translateModal(self):
		"""This is only reached if the modal is stand-alone, so just do him by himself"""
		
		#just set our tense to the tense of our modal
		form = self.verb.verb.get(True)[0]
		stem = self.verb.verb.getStem()
		
		#some modals have the same subj2 / preterite form -> I have no way to differentiate
		if (stem == form["subj2"] and stem == form["preterite"]):
			self.setTense(tenses.CONDITIONAL_PAST + " OR " + tenses.PRETERITE)
		elif (stem == form["subj2"]):
			self.setTense(tenses.CONDITIONAL_PAST)
		elif (stem in (form["first"], form["third"], form["stem"])):
			self.setTense(tenses.PRESENT)
		elif (stem == form["preterite"]):
			self.setTense(tenses.PRETERITE)
		
		self.__doTranslations(form["full"])
	
	def __translateWithParent(self, parent):
		"""Do a translation when our parent is a helper"""
		
		if (self.verb.verb.isModal()):
			#if we're a modal, and so is our parent
			if (parent.verb.verb.isModal()):
				self.__translateWithHelper_modal(parent)
			
			#otherwise, we're a modal and our parent is a helper
			else:
				self.__translateWithModal_helper(parent)
			
			#if we have two modals in a row, then we're doing something crazy
			#and need to change the translation of our child verb, provided our
			#child is not a helper with a child (ie. it's a standalone helper)
			if (parent.verb.verb.isModal() and not (self.child.verb.isHelper() and self.child.child != None)):
				self.child.__translateInheritedTense_modal(parent)
			
			#we need to determine how to translate our child
			#if the child is a helper, then let him route normally
			#if he isn't, then he needs to inherit the tense from us
			elif (self.child != None and self.child.verb.isHelper()):
				self.child.translate()
			elif (self.child != None
				and self.conjugation.word == word.canoo.helperWerden
				and self.verb.isHelper()
			):
				self.translate()
			elif (self.child != None):
				self.child.__translateInheritedTense_helper(parent)
			
		#in german, you can't have two helpers in a row (unless you're doing the FuturII tense...but
		#that's just confusion anyway)
		else:
			self.__translateWithHelper(parent)
	
	def __translateInheritedTense_helper(self, uberParent):
		"""
		Translates an inherited tense.  When we get here, it means we're doing something like:
			
			"Ich hätte sprechen sollen" -> "I should have spoken"
			
		Typically, since sprechen is in infinitive, it doesn't really have a tense as it's not
		being directly modified by anything.  Therefore, we need to observe the parent tense
		and use that to figure out our tense.
		
		We're taking the uberParent (the parent of our parent) in order to figure this information
		out as that is where the tense information is coming from.
		"""
		
		form = uberParent.verb.verb.get(True)[0]
		stem = uberParent.verb.verb.getStem()
		
		#this is the only case I can think of right now, more to come, I'm sure
		if (form["subj2"] == stem):
			self.setTense(tenses.PAST_PERFECT)
		
		#and add our translations to the output
		for v in self.conjugation.verb.get(True):
			self.__doTranslations(v["full"])
	
	def __translateInheritedTense_modal(self, uberParent):
		"""
		Translates an inherited tense.  When we get here, it means we're doing something like:
			
			"Ich würde bleiben müssen" -> "I would have to stay"
		"""
		
		form = uberParent.verb.verb.get(True)[0]
		stem = uberParent.verb.verb.getStem()
		
		#this is the only case I can think of right now, more to come, I'm sure
		if (form["subj2"] == stem):
			self.setTense(tenses.INFINITIVE)
		
		#and add our translations to the output
		for v in self.conjugation.verb.get(True):
			trans = word.word(v["full"]).get("verb")
			self.__meaning(trans, v["full"])
		
	def __translateWithHelper_modal(self, parent):
		form = parent.conjugation.verb.get(True)[0]
		stem = parent.conjugation.verb.getStem()
		
		if (stem == form["subj2"]):
			self.setTense(tenses.CONDITIONAL)
		elif (stem in (form["first"], form["third"], form["stem"])):
			self.setTense(tenses.PAST_PERFECT)
		
	def __translateWithModal_helper(self, parent):
		form = parent.conjugation.verb.get(True)[0]
		stem = parent.conjugation.verb.getStem()
		
		#probably more to be added in the future
		if (stem == form["subj2"]):
			self.setTense(tenses.CONDITIONAL_PAST)
		
		self.__doTranslations(self.verb.verb.get(True)[0]["full"])
		
	def __translateWithHelper(self, parent):
		#grab our helper's conjugations and stuff
		helperConj = parent.verb.verb.getStem()
		helper = parent.verb.verb.get(unknownHelper = True)[0]
		
		#if we're going for simple tenses
		if (helper["stem"] == "hab" or helper["stem"] == "sein"):
			#it's possible that we have numerous verbs that take the same past-tense form
			verbs = []
			stem = self.conjugation.verb.getStem()
			
			#is the verb in the right form for having a helper?
			#check here to make sure that the entered verb is in the right past-tense form
			for v in self.conjugation.verb.get(helper = helper["full"]):
				#make sure we have the right helper, too
				if (v["perfect"] == stem and v["hilfsverb"] == helper["full"]):
					verbs.append(word.word(v["full"]))
			
			#two loops...otherwise things get far too indented and painful
			for v in verbs:
				used = False
				
				#process the translation into its proper output form
				if (helperConj in (helper["third"], helper["first"], helper["stem"])):
					self.setTense(tenses.PAST_PERFECT)
					used = True
				elif (helperConj == helper["subj2"]):
					self.setTense(tenses.CONDITIONAL_PAST)
					used = True
				elif (helperConj == helper["preterite"]):
					self.setTense(tenses.PLUSQUAM)
					used = True
				
				#and set the translations with the full form of our word
				#it can grab from our node the conjugated values, &etc.
				if (used):
					self.__doTranslations(v.word)
		
		#this is a special-case tense -> the combination of a helper and a modal...owwies
		elif (helper["stem"] == "werd"
			and self.verb.word in (word.canoo.helperHaben, word.canoo.helperSein)
			and self.child != None
			and self.child.conjugation.verb.getStem() == self.child.conjugation.verb.get(True)[0]["perfect"]
		):
			self.child.setTense(tenses.FUTURE2)
			self.child.__doTranslations(self.child.conjugation.verb.get(True)[0]["full"])
		#something going on with werden -> conditional present, passive voice
		elif (helper["stem"] == "werd"):
			conjugatedStem = self.conjugation.verb.getStem()
			
			#all the possible verbs (ex: gedenken + denken for gedacht)
			for v in self.conjugation.verb.get(helper["full"]):
				used = False
				#if we're looking at an unconjugated form of the verb: sehen
				if (conjugatedStem == v["stem"]):
					if (helperConj == helper["subj2"]):
						self.setTense(tenses.CONDITIONAL)
						used = True
					elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
						self.setTense(tenses.FUTURE)
						used = True
				elif (conjugatedStem == v["perfect"]):
					if (helperConj == helper["preterite"]):
						self.setTense(tenses.PASSIVE_PAST)
						used = True
					elif (helperConj in (helper["third"], helper["first"], helper["stem"])):
						self.setTense(tenses.PASSIVE_PRESENT)
						used = True
				
				if (used):
					self.__doTranslations(v["full"])
	
	def __setNormalTenses(self, forms, stem):
		"""
		When there aren't any special cases, and the verb follows the tense forms exactly, this is
		a quick way to set the tense.
		"""
		
		for form in forms:
			used = False
			
			if (stem == form["subj2"] and stem == form["preterite"]):
				self.setTense(tenses.CONDITIONAL_PAST + " OR " + tenses.PRETERITE)
				used = True
			elif (stem == form["subj2"]):
				self.setTense(tenses.CONDITIONAL_PAST)
				used = True
			elif (stem in (form["first"], form["third"], form["stem"])):
				self.setTense(tenses.PRESENT)
				used = True
			elif (stem == form["preterite"]):
				self.setTense(tenses.PRETERITE)
				used = True
			
			if (used):
				self.__doTranslations(form["full"])
	
	def __doTranslations(self, fullForm):
		if (not verbNode.doTranslations):
			return
		
		#check if we're a `kennen lernen` type guy
		toTranslate = fullForm
		if (self.conjugation.word != self.verb.word):
			words = self.verb.word.split(" ")
			#get the original form of the word
			words[len(words) - 1] = self.conjugation.word
			toTranslate = " ".join(words)
		
		trans = word.word(toTranslate).get("verb")
		self.__meaning(trans, fullForm)
	
	def __meaning(self, translations, fullForm):
		"""Puts the translations into the output dictionary list."""
		
		#only add meanings if we have a tense
		#otherwise, we're nothing
		if (self.tense == None):
			return
		
		#if we have a `kennen lernen` type verb going on
		origWord = self.verb.word
		if (self.conjugation.word != origWord):
			words = self.verb.word.split(" ")
			#get the original form of the word
			words[len(words) - 1] = self.conjugation.word
			origWord = " ".join(words)
			
			#get the full form of the word
			fullForm = self.verb.word
			
		for t in translations:
			d = dict({
				"en": "(" + self.tense + ") " + t["en"],
				"de": fullForm,
				"deOrig": origWord,
				"deWordLocation": self.verb.sentLoc
			})
			
			if (d not in self.meanings):
				self.meanings.append(d)
	
	def dump(self):
		#arg, python2.4!
		tense = self.tense
		if self.tense == None:
			tense = "helper"
			
		print self.verb.word + " (" + tense + ")",
		if (self.child != None):
			print " ->  ",
			self.child.dump()
