# -*- coding: utf-8 -*-

from config import config
import urllib
import re
from pyquery import PyQuery as pq

from mysql import mysql
import translator

def resolveWord(word):
	"""Attempts to find a good translation for the word"""
	
	#step 1: run a lookup for common german stuff that we already know
	local = lookuper(word)
	if (local.exists()):
		return local.get()

	#step 2: we couldn't find it, so run some of the harder stuff against it
	translator.setQuery(word)
	if (translator.canTranslate()):
		return translator.translate()
	
	#step 3: if we still can't find it, it just doesn't exist...
	return ()

class lookuper(object):
	def __init__(self, word):
		self.cache = cacher(word)
		self.scrape = scraper(word, self.cache)
	
	def exists(self):
		#step 1: hit our cache to see if we have the word already translated
		self.cacheExists = self.cache.exists()
		
		#don't hit the internet unless we absolutely need to
		#im not sure if I should also not hit the interwebs if found=0 -- in the future, if a definition is added
		#this would prevent me from hitting the net, so for now, I'm going to let it continue to hit the site on
		#every miss, and then go from there
		if (not self.cacheExists):
			#step 2: if it's not in our cache, check to see if we can locate it online
			self.scrapeExists = self.scrape.exists()
		
		return self.cacheExists or self.scrapeExists
		
	def get(self):
		if (self.cacheExists):
			return self.cache.get()
		elif (self.scrapeExists):
			return self.scrape.get()
		else:
			return () #if the programmer does something stupid, just return an empty set

class data(object):
	def __init__(self):
		self.db = mysql.getInstance()
	
class cacher(data):
	"""Controls the cache of words that we have already solved"""
	
	searchRan = False
	
	def __init__(self, word):
		super(cacher, self).__init__()
		self.word = word
	
	def exists(self, found = 1):
		"""Checks to see if we have a cache of the word"""
		return config.getboolean("deutsch", "enable.cache") and self.db.query('SELECT 1 FROM `searches` WHERE `text`=%s AND `found`=%s;', (self.word, found))
	
	def get(self):
		"""Gets a list of words from the cache based on the search"""
		
		words = self.db.query('SELECT * FROM `words` WHERE `en`=%s OR `de`=%s;', (self.word, self.word))
		
		if (type(words) != tuple):
			return () #return an empty list...there's nothing anyway
		
		return [word(db = w) for w in words]
		
	def stash(self, words):
		"""Saves the list of words retrieved from the internet to our cache"""
		
		if (not config.getboolean("deutsch", "enable.cache")):
			return
		
		if ((self.exists(0) and len(words) == 0) or self.exists(1)):
			return
		
		#first, save our search -- this is what we check to see if exists()
		self.db.query("""
			INSERT INTO `searches`
			SET
				`text`=%s,
				`found`=%s
			;
			""",
			(self.word, bool(len(words) > 1))
		)
		
		for w in words:
			info = (w["en"], w["en-ext"], w["de"], w["de-ext"], w["pos"])
			
			sql = """
				SELECT 1 FROM `words`
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
			"""
			#only insert the row if it doesn't exist already (from another lookup)
			if (not self.db.query(sql, info)):
				self.db.query("""
					INSERT INTO `words`
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

class scraper(data):
	"""Controls access to words on the interwebs"""
	
	searchRan = False
	
	def __init__(self, word, cacher):
		super(scraper, self).__init__()
		self.word = word.encode('utf-8')
		self.cacher = cacher
	
	def __isWord(self, word, row):
		"""Given a word, tests if it is actually the word we are looking for.
		
		Online, there will be some definitions like this (eg. for "test"):
			test - to pass a test, to carry out a test, and etc
		
		We are only concerned with the actual word, "test", so we ignore all the others."""
		
		if (row.get("en") == word or row.get("de") == word):
			return True
		
		return False
	
	def get(self):
		"""Grabs our cache of the last search"""
		
		self.__search()
		return self.translations
	
	def __search(self):
		"""Checks the interwebs to see if the word can be found there"""
		
		if (self.searchRan):
			return
		
		self.searchRan = True
		
		searchKey = self.word
		
		d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % urllib.quote(searchKey))
		
		#todo - We're going to have to branch here for sentences / phrases vs words
		
		rows = [word(en = pq(row[1]), de = pq(row[3])) for row in d.find("tr[valign=top]")]
		
		self.translations = [row for row in rows if self.__isWord(searchKey, row)]
		
		#and cache this search
		self.cacher.stash(self.translations)
	
	def exists(self):
		"""Sees if the given word can be found online"""
		
		self.__search()
		return config.getboolean("deutsch", "enable.scrape") and (len(self.translations) > 0)

class word:
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
		
		#and save our dictionary
		self.translations = row

	def createWordFromPq(self, words):
		"""Given a pyquery object, creates and cleans up the translations"""
		
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
