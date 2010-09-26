# -*- coding: utf-8 -*-

from config import config
import urllib
import re
from pyquery import PyQuery as pq
import time

from mysql import mysql
import translator

def resolveWord(word):
	"""Attempts to find a good translation for the word"""
	
	#step 1: run a lookup for common german stuff that we already know
	local = lookup(word)
	if (local.exists()):
		return local.get()

	#step 2: we couldn't find it, so run some of the harder stuff against it
	translator.setQuery(word)
	if (translator.canTranslate()):
		return translator.translate()
	
	#step 3: if we still can't find it, it just doesn't exist...
	return ()

class data(object):
	def __init__(self):
		self.db = mysql.getInstance()

#####################################################
#####################  Info  ########################
#####################################################
###  The following are the classes that function  ###
###         on local/internet words               ###
#####################################################

class lookup(data):
	"""Controls access to words on the interwebs. Contains a collection of individual words."""
	
	searchRan = False
	
	def __init__(self, word):
		super(lookup, self).__init__()
		self.word = word
		self.cache = cacher(word)
	
	def isAdjAdv(self):
		return self.__isA("adjadv")
	
	def isNoun(self):
		return self.__isA("noun")
	
	def isVerb(self):
		return self.__isA("verb")
		
	def __isA(self, pos):
		words = self.get()
		if (len(words) == 0):
			return False
		
		return bool(len([w for w in words if w["pos"] == pos]) > 0)
	
	def __isWord(self, word, row):
		"""Given a word, tests if it is actually the word we are looking for.
		
		Online, there will be some definitions like this (eg. for "test"):
			test - to pass a test, to carry out a test, and etc
		
		We are only concerned with the actual word, "test", so we ignore all the others."""
		
		word = word.lower()
		
		#i'm allowing three spaces before i throw a word as out invalid
		if (len(row.get("en").split(" ")) > 3 or len(row.get("de").split(" ")) > 3):
			return False
		
		if (row.get("en").lower() == word or row.get("de").lower() == word):
			return True
		
		return False
	
	def get(self, pos = "all"):
		"""Grabs our cache of the last search"""
		
		self.__search()
		
		if (pos in ['adjadv', 'noun', 'verb']):
			return [t for t in self.translations if t["pos"] == pos]
		else:
			return self.translations
	
	def getWord(self):
		return self.word
	
	def __search(self):
		"""Checks the interwebs to see if the word can be found there"""
		
		if (self.searchRan):
			return
		
		self.searchRan = True
		
		#check our cache to see if it's already there
		if (self.cache.exists()):
			self.translations = self.cache.get()
		elif (not self.cache.exists(0)): #don't hit the internet every time we have a miss -- if it's a miss, move on
			searchKey = self.word
			
			d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % urllib.quote(searchKey))
			
			rows = [word(en = pq(row[1]), de = pq(row[3])) for row in d.find("tr[valign=top]")]
			
			self.translations = [row for row in rows if self.__isWord(searchKey, row)]
			
			#and cache this search
			self.cache.stash(self.translations)
		else:
			self.translations = ()
	
	def exists(self):
		"""Sees if the given word can be found online"""
		
		self.__search()
		return config.getboolean("deutsch", "enable.scrape") and (len(self.translations) > 0)

class cacher(data):
	"""Controls the cache of words that we have already solved"""
	
	searchRan = False
	
	def __init__(self, word):
		super(cacher, self).__init__()
		self.word = word
	
	def exists(self, found = 1):
		"""Checks to see if we have a cache of the word"""
		return config.getboolean("deutsch", "enable.cache") and self.db.query('SELECT 1 FROM `searches` WHERE `text`=%s AND `found`=%s AND `type`="LEO";', (self.word, found))
	
	def get(self):
		"""Gets a list of words from the cache based on the search"""
		
		words = self.db.query('SELECT * FROM `leoWords` WHERE `en`=%s OR `de`=%s;', (self.word, self.word))
		
		if (type(words) != tuple):
			return () #return an empty list...there's nothing anyway
		
		return [word(db = w) for w in words]
		
	def stash(self, words):
		"""Saves the list of words retrieved from the internet to our cache"""
		
		if (not config.getboolean("deutsch", "enable.cache")):
			return
		
		if ((len(words) == 0 and self.exists(0)) or self.exists(1)):
			return
		
		#first, save our search -- this is what we check to see if exists()
		self.db.insert("""
			INSERT INTO `searches`
			SET
				`text`=%s,
				`found`=%s,
				`type`="LEO"
			;
			""",
			(self.word, bool(len(words) >= 1))
		)
		
		for w in words:
			info = (w["en"], w["en-ext"], w["de"], w["de-ext"], w["pos"])
			
			sql = """
				SELECT 1 FROM `leoWords`
				WHERE
					`en`=%s
					AND
					`en-ext`=%s
					AND
					`de`=%s
					AND
					`de-ext`=%s
					AND
					`pos`=%s
				;
			"""
			#only insert the row if it doesn't exist already (from another lookup)
			if (not self.db.insert(sql, info)):
				self.db.query("""
					INSERT INTO `leoWords`
					SET
						`en`=%s,
						`en-ext`=%s,
						`de`=%s,
						`de-ext`=%s,
						`pos`=%s
					;
					""",
					info
				)

class word:
	"""
	A wrapper for a word-string: allows operations on the word to get it to its base and get more
	information about it.
	"""
	
	extended = False
	
	#words that need a space after them in order to be removed
	spaceWords = ["der", "die", "das", "to", "zu", "zur", "zum"]
	
	#words to always remove
	unspacedWords = ["sth.", "etw.", "jmdm.", "jmdn.", "so."]
	
	#words that can have a space before or after to remove
	#and stupid python 2.* requires unicode strings for anything fun...ugh
	egalSpace = ["bis", "durch", "entlang", u"für", "gegen", "ohne", "um", "aus", "ausser",
		u"außer", "bei", "beim", u"gegenüber", "mit", "nach", "seit", "von", "zu",
		"an", "auf", "hinter", "in", "neben", u"über", "unter", "vor", "zwischen",
		"statt", "anstatt", "ausserhalb", u"außerhalb", "trotz", u"während", "wegen"
	]
	
	def __init__(self, **words):
		self.translations = dict()
		
		if ("db" in words):
			self.createWordFromDb(words["db"])
		else:
			self.createWordFromPq(words)

	def createWordFromDb(self, row):
		"""Given a row from the database, assumes the cols are properly formed, and creates the proper word"""
		
		#get rid of our id row, prepare for easy transition to new dictionary format
		del row["id"]
		
		#and save our dictionary (everything from the database is already utf8)
		self.translations = row

	def createWordFromPq(self, words):
		"""Given a pyquery object, creates and cleans up the translations"""
		
		#be sure everything we accept is encoded in utf8 -- otherwise, our compares get screwed up
		for k, v in words.iteritems():
			#since we accept both string and pyquery, we have to clean both
			if (type(v) == pq):
				self.translations[k + "-ext"] = v.text().encode('utf-8')
			else:
				self.translations[k + "-ext"] = v.encode('utf-8')
			
			self.translations[k] = self.__cleanWord(v).encode('utf-8')
		
		#find out the part of speech of this one
		de = self.translations["de-ext"]
		en = self.translations["en-ext"]
		if (en.find("prep.") >= 0):
			pos = "prep"
		elif (en.find("to ") >= 0):
			pos = "verb"
		elif (de.find("der") >= 0 or de.find("die") >= 0 or de.find("das") >= 0):
			pos = "noun"
		else:
			pos = "adjadv"
		
		self.translations["pos"] = pos	
	
	@classmethod
	def showExtended(cls, option, opt, value, parser):
		cls.extended = True
	
	def keys(self):
		return self.translations.keys()
	
	def __getitem__(self, key):
		"""Returns a display of the word as the user requests (extended or tiny)"""
		
		if (word.extended):
			return self.translations[key + "-ext"]
		
		return self.translations[key]
	
	def get(self, key):
		"""Bypasses the extended functionality and returns what was originally entered"""
		
		return self.translations[key]
	
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
		
		#remove anything following a dash surrounded by spaces -- this does not remove things that END in dashes
		loc = word.find(" -")
		if (loc >= 0):
			word = word[:loc]
		
		#get rid of the extra words that aren't needed but that could possibly conflict with strings inside other words (so give them a trailing space)
		for w in self.spaceWords:
			word = word.replace(w + " ", "").strip()
		
		#and the words that aren't needed and can't conflict with other words
		for w in self.unspacedWords:
			word = word.replace(w, "").strip()
		
		#now, let's lose the hanging words that just get in the way
		for w in self.egalSpace:
			word = word.replace(w + " ", "").replace(" " + w, "").strip()
		
		#remove anything following a "|"
		loc = word.find("|")
		if (loc >= 0):
			word = word[:loc]
		
		return word.strip("-").strip()

#####################################################
#####################  Info  ########################
#####################################################
###  The following are the classes that function  ###
###           specifically on verbs.              ###
#####################################################

class deVerb(object):
	def __init__(self, verb):
		self.verb = verb
	
	def getStem(self):
		ret = self.verb
		
		#start by removing any endings we could have when conjugated
		for end in ["est", "et", "en", "e", "st", "t"]: #order matters in this list
			if (ret[len(ret) - len(end):] == end): #remove the end, but only once (thus, rstrip doesn't work)
				ret = ret[:len(ret) - len(end)]
				break
		
		if (type(ret) == str):
			ret = unicode(ret, "utf8")
		
		return ret
	
	def getString(self):
		return self.verb
	
	def __str__(self):
		return self.verb
	
	def __unicode__(self):
		return unicode(self.verb)
	
	def __eq__(self, other):
		"""Make string compares on verbs work"""
		return self.verb == unicode(other.decode("utf-8"))

class inflexion(object):
	def __init__(self, **inflect):
		self.inflect = inflect
	
	def __getitem__(self, key):
		return self.inflect[key]

class canoo(data):
	"""Controls access to canoo's database on the interwebs"""

	searchRan = False
	
	#the last time a canoo page was loaded
	lastCanooLoad = -1
	
	#seems to load fine after a second
	canooWait = 1
	
	#external definitions for the helper verbs
	helper = "haben"
	helperHaben = "haben"
	helperSein = "sein"
	
	def __init__(self, word):
		super(canoo, self).__init__()
		self.verb = deVerb(word)
		self.cache = canooCacher(self.verb)
	
	def setHelper(self, helper):
		if (helper != self.helperSein and helper != self.helperHaben):
			helper = self.helperHaben
		
		self.helper = helper
	
	def exists(self):
		self.__search()
		return (len(self.inflexions) > 0)
	
	def getVerb(self):
		return self.verb
	
	def get(self, unknownHelper = False):
		self.__search()
		
		if (self.helper not in self.inflexions.keys()):
			if (unknownHelper and len(self.inflexions.keys()) > 0): #if we don't know the helper, return whatever we have
				return self.inflexions[self.inflexions.keys()[0]]
			
			#the list was empty, just die
			return ()
		
		return self.inflexions[self.helper]
	
	def __search(self):
		if (self.searchRan):
			return
		
		self.searchRan = True
		
		if (self.cache.exists()):
			self.inflexions = self.cache.get()
		else:
			self.__scrapeCanoo()
	
	def __scrapeCanoo(self):
		"""Grabs the inflections of all verbs that match the query"""
		
		#hit the page
		url = url = unicode(str(self.verb).decode("utf-8"))
		for c, r in zip([u'ä', u'ö', u'ü', u'ß'], ['ae', 'oe', 'ue', 'ss']): #sadiofhpaw8oenfasienfkajsdf! urls suck
			url = url.replace(c, r)
		
		p = self.__getCanooPage('http://www.canoo.net/services/Controller?dispatch=inflection&input=%s' % urllib.quote(url))
		
		#setup our results
		self.inflexions = dict()
		
		#canoo does some different routing depending on the results for the word, so let's check what page
		#we recieved in order to verify we perform the right action on it
		if (p.find("h1.Headline").text().find(u"Keine Einträge gefunden") >= 0):
			self.inflexions = dict()
		elif (p.find("h1.Headline").text() != u"Wörterbuch Wortformen"):
			(helper, inflect) = self.__processPage(p)
			self.inflexions[helper] = inflect
		else:
			#grab the links
			links = [l for l in p.find("td.contentWhite a[href^='/services/Controller?dispatch=inflection']") if pq(l).text().find("Verb") >= 0]
			
			for a in links:
				(helper, inflect) = self.__scrapePage(a)
				self.inflexions[helper] = inflect
		
	def __scrapePage(self, a):
		"""Scrapes a page on canoo.net to find the verb forms"""
		
		#scrape the page with information about the verb
		url = pq(a).attr.href
		page = self.__getCanooPage('http://www.canoo.net/' + url)
		
		return self.__processPage(page)
	
	def __processPage(self, page):
		#just use "q" for a basic "query" holder
		
		#find the table holding the present-forms of the verb
		q = page.find("div#Presens div table tr")
		stem = deVerb(q.eq(3).find("td").eq(1).text())
		third = deVerb(q.eq(4).find("td").eq(1).text())
		
		#find the preterite
		q = page.find("div#Praeteritum div table tr")
		preterite = deVerb(q.eq(3).find("td").eq(1).text())
		subj2 = deVerb(q.eq(3).find("td").eq(3).text())
		
		#find the perfekt
		q = page.find("div#Perfect table tr")
		perfect = deVerb(q.eq(4).find("td").eq(2).text())
		
		#get the full form of the verb
		full = page.find("h1.Headline i").text()

		#attempt to get the helper verb
		helper = self.helperHaben if (page.find("div#Verb").prevAll("table").text().find("Hilfsverb: haben") != -1) else self.helperSein
		
		inflect = inflexion(full = full, helper = helper, stem = stem, preterite = preterite, perfect = perfect, third = third, subj2 = subj2)
		
		self.cache.stash(inflect)
		
		return (helper, inflect)
	
	def __getCanooPage(self, url):
		"""Canoo has mechanisms to stop scraping, so we have to pause before hit the links too much"""
		
		print url
		
		if (self.lastCanooLoad != -1 and ((time.clock() - self.lastCanooLoad) < self.canooWait)):
			time.sleep(self.canooWait - (time.clock() - self.lastCanooLoad))
			
		self.lastCanooLoad = time.clock()
		return pq(url)
		
class canooCacher(data):
	"""
	Controls the cache of words from canoo
	
	Unlike the other cacher, this will NOT save a search if nothing was found (because this never gets
	called, in that case)
	"""
	
	def __init__(self, word):
		super(canooCacher, self).__init__()
		self.verb = word
	
	def exists(self, found = 1):
		return config.getboolean("deutsch", "enable.cache") and self.db.query('SELECT 1 FROM `searches` WHERE `text`=%s AND `found`=%s AND `type`="Canoo";', (self.verb, found))
	
	def stash(self, inflect):
		if (not config.getboolean("deutsch", "enable.cache")):
			return
		
		if (not self.exists(1)):
			self.db.query("""
				INSERT INTO `searches`
				SET
					`text`=%s,
					`found`=1,
					`type`="Canoo"
				;
			""", (self.verb))
		
		found = self.db.query("""
			SELECT 1 FROM `canooWords`
			WHERE
				`full`=%s
				AND
				`hilfsverb`=%s
		""", (inflect["full"], str(inflect["helper"])))
		
		#if we don't have the word already stored....
		if (not found):
			self.db.insert("""
				INSERT INTO `canooWords`
				SET
					`full`=%s,
					`stem`=%s,
					`preterite`=%s,
					`hilfsverb`=%s,
					`perfect`=%s,
					`third`=%s,
					`subj2`=%s
				;
			""", (
				inflect["full"],
				inflect["stem"].getStem(),
				inflect["preterite"].getStem(),
				str(inflect["helper"]),
				inflect["perfect"].getStem(),
				inflect["third"].getStem(),
				inflect["subj2"].getStem()
				)
			)
		
	def get(self):
		stem = self.verb.getStem()
		
		rows = self.db.query("""
			SELECT * FROM `canooWords`
			WHERE
				`full`=%s
				OR
				`stem`=%s
				OR
				`preterite`=%s
				OR
				`perfect`=%s
				OR
				`third`=%s
				OR
				`subj2`=%s
			;
		""", (self.verb, stem, stem, stem, stem, stem))
		
		if (type(rows) != tuple):
			return () #return an empty list...there's nothing anyway
		
		words = dict()
		
		for r in rows:
			tmp = dict()
			del r['id'] #remove the id row, we don't need it
			for k, v in r.iteritems():
				tmp[k] = deVerb(v)
			
			words[r["hilfsverb"]] = tmp
		
		return words
