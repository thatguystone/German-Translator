# -*- coding: utf-8 -*-
import urllib
from pyquery import PyQuery as pq
import re
import time
import os
import codecs

from config import config
from mysql import mysql
import translator
import utf8

class word(object):
	"""Encapsulates a word to get all the information about it"""
	
	def __init__(self, word, sentLoc = -1, clauseLoc = -1, numWords = -1):
		self.word = utf8.encode(word)
		self.verb = canoo(self.word)
		self.translations = cache(self.word)
		
		#these are useful for doing calculations with word locations in sentences
		#in order to figure out if something is a verb or just a noun hanging out in
		#the middle
		self.sentLoc = sentLoc
		self.clauseLoc = clauseLoc
		self.numWords = numWords
	
	def exists(self):
		return self.translations.exists() and self.verb.exists()
	
	def get(self, pos = "all"):
		#if we have a verb, then add the root translations to the mix
		#do this on demand -- we only need this information if we're getting translations
		if (self.isVerb() or self.verb.isParticiple()):
			full = self.verb.get(unknownHelper = True)[0]["full"]
			if (full != self.word):
				self.translations.addTranslations(cache(full))
		
		return self.translations.get(pos)
	
	def isAdj(self):
		"""
		Only returns True if the adj had an ending on it.
		"""
		
		#lose the adj ending
		w = self.word
		for e in ("es", "en", "er", "em", "e"):
			if (w[len(w) - len(e):] == e): #remove the end, but only once (thus, rstrip doesn't work)
				w = w[:len(w) - len(e)]
				break
				
		#if there was no ending...just check our list
		if (w != self.word):
			return word(w).isAdj()
		else:
			return self.__isA("adjadv")
	
	def isNoun(self):
		if (len(self.word) == 0):
			return False
		
		if (self.word.isdigit()):
			return True
			
		#check to see if we are captalized -> nice indication we're a noun
		if (not (self.word[0] >= 'A' and self.word[0] <= 'Z')):
			return False
		
		isN = self.__isA("noun")
		
		if (isN):
			return True
		
		#maybe we have a plural?
		w = self.word
		for r in ("e", "en", "n", "er", "nen", "se", "s"):
			if (w[len(w) - len(r):] == r): #remove the end, but only once (thus, rstrip doesn't work)
				w = w[:len(w) - len(r)]
				break
		
		if (w != self.word and len(w) > 0 and word(w).isNoun()):
			return True
		
		#do an umlaut replace on w -- only the first umlaut becomes normal
		umlauts = (u"ü", u"ä", u"ö")
		for l, i in zip(w, range(0, len(w))):
			if (l in umlauts):
				w = w[:i] + l.replace(u"ü", "u").replace(u"ä", "a").replace(u"ö", "o") + w[i + 1:]
				break
		
		if (w != self.word and len(w) > 0 and word(w).isNoun()):
			return True
		
		return False
			
	def isVerb(self, ignoreLocation = False):
		if (self.isNoun()):
			#make sure we're not at the beginning of a sentence -- that would be embarassing
			if (self.clauseLoc != 0):
				return False
		
		#"sein" is an ambiguous word -- remove it if it has any endings
		if (self.word.lower() in ("seine", "seines", "seiner", "seinen", "seinem")):
			return False
		
		#if we exist, then check our location in the sentence to see the likelihood of being
		#a verb
		if (self.verb.exists()):
			if (ignoreLocation or self.clauseLoc == -1 or self.numWords == -1):
				return True #not much we can do, we don't have word locations, so just use what we got from canoo
			
			#check its location in the sentence
			if (self.clauseLoc <= config.getint("deutsch", "word.verbStart")
				or
				self.clauseLoc >= (self.numWords - config.getint("deutsch", "word.verbEnd"))):
					return True
			
		return False
	
	def isParticiple(self):
		return self.verb.isParticiple()
	
	def isHelper(self):
		return self.verb.isHelper()
	
	def isSeparablePrefix(self):
		"""Not much I can do about this one, we just have a long list of prefixes to check."""
		return self.word.lower() in [
			"ab", "an", "auf", "aus", "bei", "da", "dabei", "daran", "durch", "ein", "empor", "entgegen",
			"entlang", "fehl", "fest", "fort", u"gegenüber", "gleich", "her", "herauf", "hinter",
			"hinzu", "los", "mit", "nach", "statt", u"über", "um", "unter", "vor", "weg", "wider",
			"wieder", "zu", u"zurück", "zusammen", "zwischen"
		]
	
	def __isA(self, pos):
		#only check out database -- no need to do anything too crazy here...if we fail, no biggie
		words = self.translations.searchFromDB()
		if (len(words) == 0):
			return False
		
		return bool(len([w for w in words if w["pos"] == pos]) > 0)
	
	def getWord(self):
		"""Gets the original word that was entered, in its unmodified state"""
		return self.word
	
class internetInterface(object):
	"""
	Useful for things that hit the internet and store results from the queries in the local
	database.
	"""
	
	def __init__(self, word):
		self.word = word
		self.db = mysql.getInstance()
		self.hitInternet = False
		self.searchRan = False
		self.words = dict()

class cache(internetInterface):
	"""
	Caches the translation responses from the German-English dictionary; if the word is not found,
	it will attempt to look it up.
	"""
	
	def __init__(self, word):
		super(cache, self).__init__(word)
		self.dbCache = None
	
	def get(self, pos = "all"):
		self.__search()
		
		if (pos in ['adjadv', 'noun', 'verb']):
			return [t for t in self.words if t["pos"] == pos]
		
		return self.words
	
	def exists(self):
		self.__search()
		return len(self.words) > 0
	
	def addTranslations(self, cache):
		"""Given another cache object, it adds its translations to this one"""
		
		self.searchRan = True
		self.__storeWords(cache.get())
	
	def __search(self):
		if (self.searchRan):
			return
		
		self.searchRan = True
		
		#well, if we get here, then we know that we have some words stored
		words = self.searchFromDB()
		
		#if we didn't find any words in our translations table
		if (len(words) == 0):
			#before we hit the internet, make sure we haven't already searched for this and failed
			success = self.db.query("""
				SELECT `success` FROM `searches`
				WHERE
					`search`=%s
					AND
					`source`="leo"
			""", (self.word))
			
			#if we have never done this search before
			if (type(success) == bool):
				words = self.__scrapeLeo()
				self.__stashResults(words)
				if (len(words) == 0):
					return
			
			#we've done this search and failed, just fail out
			elif (not success[0]['success']):
				return
		
		#we found some words -- add them to our list
		self.__storeWords(words)
	
	def __searchFromDB_query(self, ret, arg):
		sql = """
			SELECT * FROM `translations`
			WHERE
				`de`=%s
			;
		"""
		
		rows = self.db.query(sql, arg)
		if (type(rows) != bool):
			#there's a pretty horrific bug in MySQL that doesn't seem to be getting resolved
			#any time soon -- ß = s, which is just....false...lslajsdfkjaskldfjask;ldfjsa;ldfjas;dklf
			#bug: http://bugs.mysql.com/bug.php?id=27877
			#this is a horrible work around :(
			ret += rows
	
	def searchFromDB(self):
		if (self.dbCache != None):
			return self.dbCache
		
		ret = []
		
		self.__searchFromDB_query(ret, self.word)
		
		if (self.word.find(u"ß") > -1):
			self.__searchFromDB_query(ret, self.word.replace(u"ß", "ss"))
		
		if (self.word.find("ss") > -1):
			self.__searchFromDB_query(ret, self.word.replace("ss", u"ß"))
		
		self.dbCache = ret
		
		return ret
	
	def __storeWords(self, words):
		"""
		Given a list of words, it stores them non-destructively (since we can have words from
		numerous sources that must be stored independently of each other
		"""
		
		if (type(self.words) != list):
			self.words = []
		
		for w in words:
			self.words.append(w)
	
	def __scrapeLeo(self):
		if (self.hitInternet):
			return
		
		self.hitInternet = True
		
		#now go and hit leo for the results
		word = self.word.encode("utf8")
		d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % urllib.quote(word))
		rows = []
		for row in d.find("tr[valign=top]"):
			#extended translations
			enExt = pq(row[1]).text()
			deExt = pq(row[3]).text()
			
			#simplified translations
			en = self.__cleanWord(pq(row[1]))
			de = self.__cleanWord(pq(row[3]))
			
			if (self.__isWord(en, de)):
				rows.append(dict(
					en = en,
					de = de,
					enExt = enExt,
					deExt = deExt,
					pos = self.__pos(enExt, deExt)
				))

		return rows
	
	def __stashResults(self, words):
		if (len(words) == 0):
			#nothing was found, record a failed search so we don't do it again
			self.db.insert("""
				INSERT IGNORE INTO `searches`
				SET
					`search`=%s,
					`source`="leo",
					`success`=0
				;
			""", (self.word))
		else:
			self.db.insert("""
				INSERT IGNORE INTO `searches`
				SET
					`search`=%s,
					`source`="leo",
					`success`=1
				;
			""", (self.word))
			
			for w in words:
				self.db.insert("""
					INSERT IGNORE INTO `translations`
					SET
						`en`=%s,
						`de`=%s,
						`enExt`=%s,
						`deExt`=%s,
						`pos`=%s
					;
				""", (
					w["en"],
					w["de"],
					w["enExt"],
					w["deExt"],
					w["pos"]
					)
				)
			
	def __isWord(self, en, de):
		"""Given a word, tests if it is actually the word we are looking for.
		
		Online, there will be some definitions like this (eg. for "test"):
			test - to pass a test, to carry out a test, and etc
		
		We are only concerned with the actual word, "test", so we ignore all the others."""
		
		word = self.word.lower()
		
		#i'm allowing three spaces before i throw a word as out invalid
		if (len(en.strip().split(" ")) > 3 or len(de.strip().split(" ")) > 3):
			return False
		
		if (en.lower() == word or de.lower() == word):
			return True
		
		return False
	
	def __pos(self, enExt, deExt):
		de = deExt
		en = enExt
		if (en.find("to ") >= 0):
			pos = "verb"
		elif (de.find("der") >= 0 or de.find("die") >= 0 or de.find("das") >= 0):
			pos = "noun"
		else:
			pos = "adjadv"
		
		return pos
	
	#words that need a space after them in order to be removed
	cleanupWords = [
		#words that just need spaces to be removed
		"der", "die", "das", "to", "zu", "zur", "zum", "sich", "oneself",
		
		#words that should always be removed
		"sth.", "etw.", "jmdm.", "jmdn.", "jmds.", "so.", "adj.",
		
		#funner words
		"bis", "durch", "entlang", u"für", "gegen", "ohne", "um", "aus", "ausser",
		u"außer", "bei", "beim", u"gegenüber", "mit", "nach", "seit", "von", "zu",
		"an", "auf", "hinter", "in", "neben", u"über", "unter", "vor", "zwischen",
		"statt", "anstatt", "ausserhalb", u"außerhalb", "trotz", u"während", "wegen"
	]
	
	def __cleanWord(self, word):
		"""Pulls the bloat out of the definitions of words so that we're just left with a word"""
		
		#clean up the word if we grabbed it from the web
		if (type(word) == pq):
			#remove the small stuff, we don't need it
			#be sure to clone the word so that we're not affecting other operations done on it in other functions
			word.clone().find("small").remove()
		
			#get to text for further string manipulations
			word = word.text()
		
		#remove the stuff that's in the brackets (usually just how the word is used / formality / time / etc)
		word = re.sub(r'(\[.*\])', "", word)
		#and the stuff in parenthesis
		word = re.sub(r'(\(.*\))', "", word)
		
		#remove anything following a dash surrounded by spaces -- this does not remove things that END in dashes
		loc = word.find(" -")
		if (loc >= 0):
			word = word[:loc]
		
		#remove anything following a "|" -- there's gotta be a better way to do this...meh...iteration?
		loc = word.find("|")
		if (loc >= 0):
			word = word[:loc]
		
		#see if we were given a plural that we need to purge
		loc = word.rfind(" die ")
		if (loc > 2): #just go for 2, something beyond the beginning of the string but before the end
			word = word[:loc]
		
		#remove extra words from the definition
		words = word.replace("/", " ").split(" ")
		
		#build up a new word that fits our parameters
		#easier to do this than remove words from the list
		newWord = []
		
		for w in words:
			if (len(w.strip()) > 0 and not w in self.cleanupWords):
				newWord.append(w)
			
		word = " ".join(newWord)
		
		return word.strip("/").strip("-").strip()
	
class canoo(internetInterface):
	"""
	Caches all the verb information from Canoo; if no information is found, then it goes to canoo
	to find it.
	"""
	
	#the last time a canoo page was loaded
	lastCanooLoad = -1
	
	#seems to load fine after a second
	canooWait = 5
	
	#external definitions for the helper verbs
	helper = "haben"
	helperHaben = "haben"
	helperSein = "sein"
	helperWerden = "werden"
	
	def __init__(self, word):
		super(canoo, self).__init__(word)
		
		self.prefix = ""
		
		#fake out canoo -- if we have a combined verb ("kennen lernen", etc), then just use
		#the last word of the verb as the verb
		if (word.find(" ") > 0):
			self.word = word[word.rfind(" ") + 1:]
			self.prefix = word[:word.rfind(" ") + 1]
	
	def exists(self):
		self.__search()
		return len(self.words) > 0
	
	def getStem(self, word = None):
		"""Gets the stem of the verb."""
		
		if (word == None):
			ret = self.word
		elif (type(word) == pq):
			word.find("br").replaceWith("\n")
			ret = word.text()
		else:
			ret = word
		
		if (ret.find("\n") >= 0):
			ret = ret.split("\n")[0]
		
		#clear away any extra spaces that might be hanging around
		ret = ret.strip()
		
		#start by removing any endings we could have when conjugated
		for end in ("est", "et", "en", "e", "st", "t"): #order matters in this list
			if (ret[len(ret) - len(end):] == end): #remove the end, but only once (thus, rstrip doesn't work)
				ret = ret[:len(ret) - len(end)]
				break
		
		return ret
	
	def isHelper(self, helpers = None):
		if (helpers == None):
			helpers = (canoo.helperHaben, canoo.helperSein, canoo.helperWerden)
		
		if (type(helpers) != tuple):
			helpers = (helpers, )
		
		if (self.exists()):
			for helper in helpers:
				if (self.get(unknownHelper = True)[0]["full"] == helper):
					return True
		
		return False
	
	def getStem_participle(self):
		w = self.word
		for end in ("es", "en", "er", "em", "e"):
			if (w[len(w) - len(end):] == end): #remove the end, but only once (thus, rstrip doesn't work)
				w = w[:len(w) - len(end)]
				break
		
		return w
	
	def getParticipleStem(self):
		#remove all the adjective endings from the word
		w = self.getStem_participle()
		
		
		#only hit the DB if we have a different word after cleaning
		#otherwise, use our cached stuff
		tmpWord = word(w)
		if (w != self.word and w != tmpWord.verb.getStem()):
			forms = tmpWord.verb.get(True)
		else:
			forms = self.get(True)
		
		if (len(forms) == 0):
			return (None, ())
		
		form = forms[0]
		
		return (w, form)
	
	def isPresentParticiple(self):
		stem, form = self.getParticipleStem()
		
		if (stem == None):
			return False
		
		#in order to be a participle, the stem has to come in as "participle" or "perfect"
		return (form["participle"] == stem)
	
	def isPastParticiple(self):
		stem, form = self.getParticipleStem()
		
		if (stem == None):
			return False
		
		#in order to be a participle, the stem has to come in as "participle" or "perfect"
		return (form["perfect"] == stem) or (form["perfect"] == self.getStem(stem))
	
	def isParticiple(self):
		stem, form = self.getParticipleStem()
		
		if (stem == None):
			return False
		
		#in order to be a participle, the stem has to come in as "participle" or "perfect"
		return (form["participle"] == stem or form["perfect"] == self.getStem(stem) or form["perfect"] == stem)
	
	def isModal(self):
		forms = self.get(True)
		
		if (len(forms) == 0):
			False
		
		form = forms[0]
		
		return (form["full"] in (u"mögen", "wollen", "sollen", "werden", u"können", u"müssen", u"dürfen"))
	
	def get(self, unknownHelper = False, returnAll = False, helper = ""):
		"""
		Gets the verb forms with their helpers.
		-unknownHelper = the helper is not known, just return the first matching with any helper
		-returnAll = give me everything you have
		"""
		
		self.__search()
		
		if (helper != ""):
			self.helper = helper
		
		if (returnAll):
			return self.words
		
		if (self.helper not in self.words.keys()):
			if (unknownHelper and len(self.words.keys()) > 0): #if we don't know the helper, return whatever we have
				return self.words[self.words.keys()[0]]
			
			#the list was empty, just die
			return ()
		
		return self.words[self.helper]
	
	def __searchDB(self, word):
		ret = []
		
		self.__searchDB_query(ret, word)
		
		if (self.word.find(u"ß") > -1):
			self.__searchDB_query(ret, word, u"ß", "ss")
		
		if (self.word.find(u"ss") > -1):
			self.__searchDB_query(ret, word, "ss", u"ß")
		
		return ret
	
	def __searchDB_query(self, ret, arg, find = None, replace = None):
		if (find != None and replace != None):
			arg = arg.replace(find, replace)
		
		rows = self.db.query("""
			SELECT * FROM `verbs`
			WHERE
				`full`=%s
				OR
				`stem`=%s
				OR
				`preterite`=%s
				OR
				`perfect`=%s
				OR
				`first`=%s
				OR
				`firstPlural`=%s
				OR
				`second`=%s
				OR
				`third`=%s
				OR
				`thirdPlural`=%s
				OR
				`subj2`=%s
				OR
				`participle`=%s
			;
		""", (self.word, ) + (arg, ) * 10)
		
		#!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
		#STUPID MYSQL BUG!!!!!!!!!!!!!!!!!!
		if (type(rows) != bool):
			for r in rows:
				#this is so slow :(
				items = r.values()
				if (arg in items or self.word in items):
					if (find != None and replace != None):
						tmp = dict()
						for k, v in r.iteritems():
							tmp[k] = unicode(v).replace(replace, find)
						tmp["full"] = r["full"]
						ret.append(tmp)
					else:
						ret.append(r)
	
	def __search(self):
		"""
		Attempts to get the information from the database.  If it fails, then it hits the internet as
		a last resort, unless it is stated in the database that the search failed, in which case there
		is no need to hit the internet.
		"""
		
		if (self.searchRan):
			return
			
		self.searchRan = True
		
		stem = self.getStem()
		
		#for now, we're going to allow these queries as I believe (this has yet to be tested)
		#that things will not be sped up if I move my search cache checker here -- verbs
		#come in all forms, and the chances that we did a search on the exact form we have are
		#1:6....so let's just risk it
		
		rows = self.__searchDB(stem)
		
		#if we have a participle, then let's cheat: change our stem to the stem or the participle
		#so that we're never tempted to hit the internet (unless we genuinely don't have the verb
		#in the DB)
		if (len(rows) == 0):
			stem = self.getStem_participle()
			rows = self.__searchDB(stem)
			
			#only include the rows if they are actually from the participles
			if (len(rows) > 0):
				rows = [r for r in rows if stem == r["participle"] or stem == r["perfect"]]
		
		if (len(rows) == 0 and stem != self.word):
			#it's entirely possible that we're removing verb endings too aggressively, so make a pass
			#on the original verb we were given, just for safety (and to save time -- hitting canoo
			#is INCREDIBLY expensive)
			rows = self.__searchDB(self.word)
		
		#but if we still haven't found anything...we must give up :(
		if (len(rows) == 0):
			rows = self.__scrapeCanoo()
			self.__stashResults(rows)
		
		if (len(rows) > 0):
			#run through all the returned rows
			#only do this if we have any -- otherwise, the dictionary was instantiated empty, so we're clear
			for r in rows:
				tmp = dict()
				if (r.has_key("id")): #remove the id row, we don't need it
					del r['id'] 
				
				#build up our temp list of column names (k) associated with words (v)
				for k, v in r.iteritems():
					tmp[k] = v
				
				if (not r["hilfsverb"] in self.words.keys()):
					self.words[r["hilfsverb"]] = []
				
				#set full back to the original verb with the prefix
				tmp["full"] = self.prefix + tmp["full"]
				
				#save the word to our helper verb table
				self.words[r["hilfsverb"]].append(tmp)
			
	def scrapeWoxikon(self, word = None, building = False):
		if (word != None):
			urlWord = word
			full = word
		else:
			urlWord = self.word
			full = self.word
		
		for r in ((u"ß", "%C3%9F"), (u"ä", "%C3%A4"), (u"ü", "%C3%BC"), (u"ö", "%C3%B6")):
			urlWord = urlWord.replace(r[0], r[1])
		
		url = "http://verben.woxikon.de/verbformen/%s.php" % urlWord
		
		#do we have a saved copy of the page locally?
		path = os.path.abspath(__file__ + "/../../cache/woxikon")
		fileUrl = url.replace("/", "$")
		if (os.path.exists(path + "/" + fileUrl)):
			f = codecs.open(path + "/" + fileUrl, encoding="utf-8", mode="r")
			page = pq(f.read())
			f.close()
		else:
			page = pq(url)
			time.sleep(.5)
			f = codecs.open(path + "/" + fileUrl, encoding="utf-8", mode="w")
			f.write(page.html())
			f.close()
			
		if (page.find("title").eq(0).text() == "Keine Ergebnisse"):
			if (not building):
				return []
			self.__stashResults([])
			return
		
		#the first is our verb info table
		info = page.find("#index").find("table.verbFormsTable").eq(0).find("tr")
		
		tbl = page.find("#verbFormsTable tr")
		
		stem = self.getStem(full)
		
		#there was an error on their end, ignore and move on
		if (page.html().find("SQLSTATE[21000]") > -1):
			return []
		
		if (tbl.eq(1).find("td").eq(0).text() == None):
			if (not building):
				return []
			self.__stashResults([])
			return
		
		prefix = info.eq(3).find("td").eq(0).text()
		if (prefix == None or prefix == "-" or prefix[0] == "("):
			prefix = ""
			
			wir = tbl.eq(1).find("td").eq(3).text().split(" ")
			#if we have a verb like "bleibenlassen" where we're not given the separable counterpart
			if (len(wir) > 1 and full != wir[0] and len(full.replace(wir[0], "")) > 0):
				prefix = tbl.eq(1).find("td").eq(3).text().split(" ")[1]
			
		participle = info.eq(6).find("td").eq(0).text()
		
		first = self.getStem(prefix + tbl.eq(1).find("td").eq(0).text().split(" ")[0])
		
		if (first == prefix + "-"):
			if (not building):
				return []
			self.__stashResults([])
			return
		
		firstPlural = self.getStem(prefix + tbl.eq(1).find("td").eq(3).text().split(" ")[0])
		second = self.getStem(prefix + tbl.eq(1).find("td").eq(1).text().split(" ")[0])
		third = self.getStem(prefix + tbl.eq(1).find("td").eq(2).text().split(" ")[0])
		thirdPlural = self.getStem(prefix + tbl.eq(1).find("td").eq(4).text().split(" ")[0])
		preterite = self.getStem(prefix + tbl.eq(2).find("td").eq(0).text().split(" ")[0])
		perfect = self.getStem(tbl.eq(7).find("td").eq(0).text().split(" ").pop()) #already has separable part attached
		subj2 = self.getStem(prefix + tbl.eq(6).find("td").eq(0).text().split(" ")[0])
		
		hilfsverb = tbl.eq(7).find("td").eq(3).text().split(" ")[0]
		if (hilfsverb == "sind"):
			hilfsverb = "sein"
		if (hilfsverb not in ("haben", "sein")):
			hilfsverb = "haben"
		
		#					  n
		#			|\   |  or
		#		   _| \-/ic
		#		  /    un
		#		//    ~ + \
		#	   //         |
		#	  //    \      \
		#	 |||     | .  .|
		#	///     / \___/
		#
		# sometimes, you just have to add a unicorn to make it all make sense :(
		
		ret = [dict(
			full = self.removeParens(full),
			hilfsverb = self.removeParens(hilfsverb),
			stem = self.removeParens(stem),
			preterite = self.removeParens(preterite),
			perfect = self.removeParens(perfect),
			first = self.removeParens(first),
			firstPlural = self.removeParens(firstPlural),
			second = self.removeParens(second),
			third = self.removeParens(third),
			thirdPlural = self.removeParens(thirdPlural),
			subj2 = self.removeParens(subj2),
			participle = self.removeParens(participle)
		)]
		
		if (not building):
			return ret
		else:
			self.__stashResults(ret)
	
	def removeParens(self, word):
		if (word == None):
			return None
		return word.replace("(", "").replace(")", "")
		
	def __scrapeCanoo(self):
		"""
		We're going to use canoo to resolve verbs to their infinitive forms, then we're going to hit
		Woxikon to get the verb forms.
		"""	
		
		if (self.hitInternet):
			return []
		
		self.hitInternet = True
		
		#first, check to see if we've failed on this search before
		failed = self.db.query("""
			SELECT 1 FROM `searches`
			WHERE
				`search`=%s
				AND
				`source`="canoo"
				AND
				`success`=0
		""", (self.word))
		
		if (failed):
			return []
		
		#hit the page
		url = unicode(self.word)
		for c, r in zip([u'ä', u'ö', u'ü', u'ß'], ['ae', 'oe', 'ue', 'ss']): #sadiofhpaw8oenfasienfkajsdf! urls suck
			url = url.replace(c, r)
		
		p = self.__getCanooPage('http://www.canoo.net/services/Controller?input=%s&service=canooNet' % urllib.quote(url.encode("utf-8")))
		
		#setup our results
		ret = []
		
		#make sure our list of verbs is unique
		verbs = set()
		for l in p.find("a[href^='/services/Controller?dispatch=inflection']"):
			label = pq(l).parent().parent().parent().prev().find("td").eq(0)
			if (label.text().find("Verb,") > -1):
				w = label.find("strong").text()
				#stupid fix for things like: "telefoniern / telephonieren"
				if (w.find("/") > -1):
					verbs.update([w.strip() for w in w.split("/")])
				else:
					verbs.add(w)
		
		for v in verbs:
			w = self.scrapeWoxikon(v)
			if (len(w) > 0):
				ret += w
		
		return ret
	
	def __getCanooPage(self, url):
		"""Canoo has mechanisms to stop scraping, so we have to pause before we hit the links too much"""
		
		#do we have a saved copy of the page locally?
		path = os.path.abspath(__file__ + "/../../cache/canoo")
		fileUrl = url.replace("/", "$")
		if (os.path.exists(path + "/" + fileUrl)):
			f = codecs.open(path + "/" + fileUrl, encoding="utf-8", mode="r")
			page = f.read()
			f.close()
			return pq(page)
		
		#make sure these are python-"static" (*canoo* instead of *self*)
		if (canoo.lastCanooLoad != -1 and ((time.time() - self.lastCanooLoad) < canoo.canooWait)):
			time.sleep(canoo.canooWait - (time.time() - self.lastCanooLoad))
		
		page = pq(url)
		
		i = 0
		while (page.text().find("Zu viele Anfragen in zu kurzer Zeit") > -1):
			time.sleep(canoo.canooWait + i)
			i += 1
			page = pq(url)
		
		canoo.lastCanooLoad = time.time()
		
		f = codecs.open(path + "/" + fileUrl, encoding="utf-8", mode="w")
		f.write(page.html())
		f.close()
		return page
	
	def __stashResults(self, res):
		if (len(res) == 0):
			#nothing was found, record a failed search so we don't do it again
			self.__stashSearch(self.word, 0)
		else:
			self.__stashSearch(self.word, 1)
			
			#we found some stuff, so save it to the db
			for inflect in res:
				#store every combination of "ß" and "ss" -> so that old german spellings work
				self.__stashInsert(inflect)
				
				#
				#no longer necessary -- MySQL collations suck0rz :(
				#
				#self.__stashInsert(inflect, u"ß", "ss")
				#self.__stashInsert(inflect, "ss", u"ß")
				#
				#if (inflect["full"].find(u"ß") > -1):
				#	self.__stashSearch(inflect["full"].replace(u"ß", "ss"), 1)
				#
				#if (inflect["full"].find("ss") > -1):
				#	self.__stashSearch(inflect["full"].replace("ss", u"ß"), 1)
	
	def __stashSearch(self, search, success):
		self.db.insert("""
			INSERT IGNORE INTO `searches`
			SET
				`search`=%s,
				`source`="canoo",
				`success`=%s
			;
		""", (search, success))
	
	def __stashInsert(self, inflect, find = None, replace = None):
		if (find != None and replace != None):
			tmp = dict()
			for k, v in inflect.iteritems():
				tmp[k] = v.replace(find, replace)
			
			tmp["full"] = inflect["full"]
			
			inflect = tmp
		
		self.db.insert("""
			INSERT IGNORE INTO `verbs`
			SET
				`full`=%s,
				`stem`=%s,
				`preterite`=%s,
				`hilfsverb`=%s,
				`perfect`=%s,
				`first`=%s,
				`firstPlural`=%s,
				`second`=%s,
				`third`=%s,
				`thirdPlural`=%s,
				`subj2`=%s,
				`participle`=%s
			;
		""", (
			inflect["full"],
			inflect["stem"],
			inflect["preterite"],
			inflect["hilfsverb"],
			inflect["perfect"],
			inflect["first"],
			inflect["firstPlural"],
			inflect["second"],
			inflect["third"],
			inflect["thirdPlural"],
			inflect["subj2"],
			inflect["participle"]
			)
		)
