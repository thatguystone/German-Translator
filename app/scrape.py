from pyquery import PyQuery as pq

import data

class scraper(data.data):
	"""Controls access to words on the interwebs"""

	def isWord(self, word, row):
		if (row["en"] == word or row["de"] == word):
			return True
		
		return False

	def exists(self, word):
		d = pq(url='http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=on&search=%s&relink=on' % word)
		rows = [{'en': pq(row[1]).text(), 'de': pq(row[3]).text()} for row in d.find("tr[valign=top]")]
		
		words = [row for row in rows if self.isWord(word, row)]
		
		return words
