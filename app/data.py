from config import config
import urllib
import re
from pyquery import PyQuery as pq
from mysql import mysql

def resolveWord(word):
	"""Attempts to find a good translation for the word"""
	
	#step 1: hit our cache to see if we have the word already translated
	cache = cacher(word)
	if (config.get("deutsch", "enable.cache") and cache.exists()):
		return cache.get()

	#step 2: if it's not in our cache, check to see if it's just a word (ie. not a compound)
	scrape = scraper(word, cache)
	if (config.get("deutsch", "enable.scrape") and scrape.exists()):
		return scrape.get()

	#step 3: we couldn't find it, so run some of the harder stuff against it
	
	#step 4: if we still can't find it, it's not a word...

class data(object):
	def __init__(self):
		self.db = mysql.getInstance()
	
class cacher(data):
	"""Controls the cache of words that we have already solved"""
	
	searchRan = False
	
	def __init__(self, word):
		super(cacher, self).__init__()
		self.word = word
	
	def exists(self):
		"""Checks to see if we have a cache of the words"""
		
		return self.db.query('SELECT 1 FROM `searches` WHERE `text`=%s;', self.word)
	
	def get(self):
		"""Gets a list of words from the cache based on the search"""
		
		words = self.db.query('SELECT * FROM `words` WHERE `en`=%s OR `de`=%s;', (self.word, self.word))
		
		if (type(words) != tuple):
			return () #return an empty list...there's nothing anyway
		
		return [word(db = w) for w in words]
		
	def stash(self, words):
		"""Saves the list of words retrieved from the internet to our cache"""
		
		#first, save our search -- this is what we check to see if exists()
		self.db.query('INSERT INTO `searches` SET `text`=%s;', self.word)
		
		for w in words:
			print w.translations
			self.db.query("""
				INSERT INTO `words`
				SET
					`en`=%s,
					`en-ext`=%s,
					`de`=%s,
					`de-ext`=%s
				;
				""",
				(w["en"], w["en-ext"], w["de"], w["de-ext"])
			)

class word:
	extended = False
	
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
				self.translations[k + "-ext"] = v.text()
			else:
				self.translations[k + "-ext"] = v
			
			self.translations[k] = self.__cleanWord(v)
	
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
		for w in ["der", "die", "das", "to"]:
			word = word.replace(w + " ", "")
		
		#and the words that aren't needed and can't conflict with other words
		for w in ["sth.", "etw."]:
			word = word.replace(w, "")	
		
		#remove anything following a "|"
		loc = word.find("|")
		if (loc >= 0):
			word = word[:loc]
		
		return word.strip("-").strip()

class scraper(data):
	"""Controls access to words on the interwebs"""
	
	searchRan = False
	
	def __init__(self, w, cacher):
		super(scraper, self).__init__()
		self.word = word(word = w)
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
		
		searchKey = self.word.get("word")
		
		d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % urllib.quote(searchKey))
		
		#todo - We're going to have to branch here for sentences / phrases vs words
		
		rows = [word(en = pq(row[1]), de = pq(row[3])) for row in d.find("tr[valign=top]")]
		
		self.translations = [row for row in rows if self.__isWord(searchKey, row)]
		
		#and cache this search
		self.cacher.stash(self.translations)
	
	def exists(self):
		"""Sees if the given word can be found online"""
		
		self.__search()
		return (len(self.translations) > 0)
