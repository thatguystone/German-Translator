from app import cache
from app import scrape

import displayer

class router:
	"""Provides a means of getting the word to be translated from the user"""
	
	def go(self):
		word = raw_input("Enter the word to translate: ")
		
		cacher = cache.cacher()
		scraper = scrape.scraper()
		
		#step 1: hit our cache to see if we have the word already translated
		if (cacher.exists(word)):
			displayer.showResults(word, cacher.get(word))

		#step 2: if it's not in our cache, check to see if it's just a word (ie. not a compound)
		displayer.showResults(word, scraper.exists(word))

		#step 3: we couldn't find it, so run some of the harder stuff against it
		
		#step 4: if we still can't find it, it's not a word...
