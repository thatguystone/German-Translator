from pyquery import PyQuery as pq

import data

class scraper(data.data):
	"""Controls access to words on the interwebs"""

	def isWord(self, word, row):
		"""Given a word, tests if it is actually the word we are looking for.
		
		Online, there will be some definitions like this (eg. for "test"):
			test - to pass a test, to carry out a test, and etc
		
		We are only concerned with the actual word, "test", so we ignore all the others."""
		
		if (row["en"] == word or row["de"] == word):
			return True
		
		return False
	
	def cleanWord(self, word):
		"""Pulls the bloat out of the definitions of words so that we're just left with a word"""

		#remove the small stuff, we don't need it
		#be sure to clone the word so that we're not affecting other operations done on it in other functions
		word.clone().find("small").remove()
		
		#get to text for further string manipulations
		word = word.text()
		
		#remove anything following a dash surrounded by spaces -- this does not remove things that END in dashes
		loc = word.find(" -")
		if (loc >= 0):
			word = word[:loc]
		
		#get rid of der-die-das's
		word = word.replace("der", "").replace("die", "").replace("das", "")
		
		return word.strip("-").strip()
	
	def exists(self, word):
		"""Checks the interwebs to see if the word can be found there"""
		
		d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % word)
		
		#todo - We're going to have to branch here for sentences / phrases vs words
		
		rows = [{
			'en': self.cleanWord(pq(row[1])),
			'en-ext': pq(row[1]).text(),
			'de': self.cleanWord(pq(row[3])),
			'de-ext': pq(row[3]).text()
			} for row in d.find("tr[valign=top]")
		]
		
		words = [row for row in rows if self.isWord(word, row)]
		
		return words
