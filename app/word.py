# -*- coding: utf-8 -*-
from config import config
import urllib
import re
from pyquery import PyQuery as pq
import time

from mysql import mysql
import translator
import utf8

class word(object):
	"""Encapsulates a word to get all the information about it"""
	
	def __init__(self, word, loc = -1, numWords = -1):
		self.word = utf8.encode(word)
		self.verb = canoo(self.word)
		self.translations = cache(self.word)
		
		#these are useful for doing calculations with word locations in sentences
		#in order to figure out if something is a verb or just a noun hanging out in
		#the middle
		self.loc = loc
		self.numWords = numWords
	
	def exists(self):
		return self.translations.exists() or self.verb.exists()
	
	def get(self, pos = "all"):
		#if we have a verb, then add the root translations to the mix
		#do this on demand -- we only need this information if we're getting translations
		if (self.isVerb()):
			full = self.verb.get(unknownHelper = True)[0]["full"]
			if (full != self.word):
				self.translations.addTranslations(cache(full))
		
		return self.translations.get(pos)
	
	def isAdjAdv(self):
		return self.__isA("adjadv")
	
	def isNoun(self):
		return self.__isA("noun")
	
	def isVerb(self):
		#check to see if we are captalized -> nice indication we're not a verb
		if (self.word[0] >= 'A' and self.word[0] <= 'Z'):
			#make sure we're not at the beginning of a sentence -- that would be embarassing
			if (self.loc != 0):
				return False
		
		#if we exist, then check our location in the sentence to see the likelihood of being
		#a verb
		if (self.verb.exists()):
			if (self.loc == -1 or self.numWords == -1):
				return True #not much we can do, we don't have word locations, so just use what we got from canoo
			
			#check its location in the sentence
			loc = self.loc / self.numWords #get a fraction of where we are
			if ((config.getfloat("deutsch", "word.verbStart") / 100) < loc or
				(1 - (config.getfloat("deutsch", "word.verbEnd") / 100)) > loc):
					return True
			
		return False
	
	def isHelper(self):
		return self.verb.isHelper()
		
	def __isA(self, pos):
		words = self.translations.get()
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
		
		self.__search()
		self.__storeWords(cache.get())
	
	def __search(self):
		if (self.searchRan):
			return
		
		self.searchRan = True
		
		#before we do anything, make sure we haven't already searched for this and failed
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
		elif (not success[0]['success']):
			return
		
		#well, if we get here, then we know that we have some words stored
		words = self.db.query("""
			SELECT * FROM `leoWords`
			WHERE
				`en`=%s
				OR
				`de`=%s
			;
		""", (self.word, self.word))
		
		self.__storeWords(words)
	
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
					INSERT IGNORE INTO `leoWords`
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
		if (en.find("prep.") >= 0):
			pos = "prep"
		elif (en.find("to ") >= 0):
			pos = "verb"
		elif (de.find("der") >= 0 or de.find("die") >= 0 or de.find("das") >= 0):
			pos = "noun"
		else:
			pos = "adjadv"
		
		return pos
	
	#words that need a space after them in order to be removed
	cleanupWords = [
		#words that just need spaces to be removed
		"der", "die", "das", "to", "zu", "zur", "zum", "sich",
		
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
		words = word.split(" ")
		for w in words:
			if (len(w.strip()) == 0):
				words.remove(w)
			else:
				#and the words that aren't needed and can't conflict with other words
				for replace in self.cleanupWords:
					if (w == replace):
						words.remove(replace)
						break

		word = " ".join(words)
		
		return word.strip("/").strip("-").strip()
	
class canoo(internetInterface):
	"""
	Caches all the verb information from Canoo; if no information is found, then it goes to canoo
	to find it.
	"""
	
	#the last time a canoo page was loaded
	lastCanooLoad = -1
	
	#seems to load fine after a second
	canooWait = 1
	
	#external definitions for the helper verbs
	helper = "haben"
	helperHaben = "haben"
	helperSein = "sein"
	helperWerden = "werden"
	
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
		
		#start by removing any endings we could have when conjugated
		for end in ("est", "et", "en", "e", "st", "t"): #order matters in this list
			if (ret[len(ret) - len(end):] == end): #remove the end, but only once (thus, rstrip doesn't work)
				ret = ret[:len(ret) - len(end)]
				break
		
		return ret
	
	def isHelper(self):
		if (self.exists()):
			for helper in (canoo.helperHaben, canoo.helperSein, canoo.helperWerden):
				if (self.get(unknownHelper = True)[0]["full"] == helper):
					return True
		
		return False
	
	def get(self, unknownHelper = False, returnAll = False):
		"""
		Gets the verb forms with their helpers.
		-unknownHelper = the helper is not known, just return the first matching with any helper
		-returnAll = give me everything you have
		"""
		
		self.__search()
		
		if (returnAll):
			return self.words
		
		if (self.helper not in self.words.keys()):
			if (unknownHelper and len(self.words.keys()) > 0): #if we don't know the helper, return whatever we have
				return self.words[self.words.keys()[0]]
			
			#the list was empty, just die
			return ()
		
		return self.words[self.helper]
	
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
		""", (self.word, stem, stem, stem, stem, stem))
		
		if (type(rows) != tuple):
			#it's entirely possible that we're removing verb endings too aggressively, so make a pass
			#on the original verb we were given, just for safety (and to save time -- hitting canoo
			#is INCREDIBLY expensive)
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
			""", (self.word, self.word, self.word, self.word, self.word, self.word))
		
		#but if we still haven't found anything...we must give up :(
		if (type(rows) != tuple):
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
				
				#save the word to our helper verb table
				self.words[r["hilfsverb"]].append(tmp)
	
	def __scrapeCanoo(self):
		"""Grabs the inflections of all verbs that match the query"""
		
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
		
		p = self.__getCanooPage('http://www.canoo.net/services/Controller?dispatch=inflection&input=%s' % urllib.quote(url.encode("utf-8")))
		
		#setup our results
		ret = []

		#canoo does some different routing depending on the results for the word, so let's check what page
		#we recieved in order to verify we perform the right action on it
		if (p.find("h1.Headline").text() != u"Wörterbuch Wortformen"):
			if(p.find("h1.Headline").text().find(u"Keine Einträge gefunden") >= 0
				or
				p.find("div#Verb").text() == None
			):
				pass #nothing found
			else:
				ret.append(self.__processPage(p))
		else:
			#grab the links
			links = [l for l in p.find("td.contentWhite a[href^='/services/Controller?dispatch=inflection']") if pq(l).text().find("Verb") >= 0]
			
			#append all the information from all the pages we found in the search
			for a in links:
				ret.append(self.__scrapePage(a))
		
		return ret
			
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
		third = self.getStem(q.eq(5).find("td").eq(1))
		
		#find the preterite
		q = page.find("div#Praeteritum div table tr")
		preterite = self.getStem(q.eq(3).find("td").eq(1))
		subj2 = self.getStem(q.eq(3).find("td").eq(3))
		
		#find the perfekt
		q = page.find("div#Perfect table tr")
		perfect = self.getStem(q.eq(4).find("td").eq(2))
		
		#get the full form of the verb
		full = page.find("h1.Headline i").text()
		
		#the stem is just the full form, minus the -en
		stem = self.getStem(full)
		
		#attempt to get the helper verb
		helper = self.helperHaben if (page.find("div#Verb").prevAll("table").text().find("Hilfsverb: haben") != -1) else self.helperSein
		
		return dict(full = full, hilfsverb = helper, stem = stem, preterite = preterite, perfect = perfect, third = third, subj2 = subj2)
	
	def __getCanooPage(self, url):
		"""Canoo has mechanisms to stop scraping, so we have to pause before hit the links too much"""
		
		#make sure these are python-"static" (*canoo* instead of *self*)
		if (canoo.lastCanooLoad != -1 and ((time.clock() - self.lastCanooLoad) < canoo.canooWait)):
			time.sleep(canoo.canooWait - (time.clock() - self.lastCanooLoad))
			
		canoo.lastCanooLoad = time.clock()
		return pq(url)
	
	def __stashResults(self, res):
		if (len(res) == 0):
			#nothing was found, record a failed search so we don't do it again
			self.db.insert("""
				INSERT IGNORE INTO `searches`
				SET
					`search`=%s,
					`source`="canoo",
					`success`=0
				;
			""", (self.word))
		else:
			self.db.insert("""
				INSERT IGNORE INTO `searches`
				SET
					`search`=%s,
					`source`="canoo",
					`success`=1
				;
			""", (self.word))
			
			#we found some stuff, so save it to the db
			for inflect in res:
				self.db.insert("""
					INSERT IGNORE INTO `canooWords`
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
					inflect["stem"],
					inflect["preterite"],
					inflect["hilfsverb"],
					inflect["perfect"],
					inflect["third"],
					inflect["subj2"]
					)
				)
