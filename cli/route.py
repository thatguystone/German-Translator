from app import data
import displayer

from optparse import OptionParser

class router:
	"""Provides a means of getting the word to be translated from the user"""
	
	def go(self):
		"""Routes the command through the application"""
		
		self.setupOptions()
		
		word = raw_input("Enter the word to translate: ")
		
		displayer.showResults(word, data.resolveWord(word))
		
	def setupOptions(self):
		"""Contains the command line option parser"""
		
		parser = OptionParser()
		
		parser.add_option("-e", "--extended-results",
			action="callback", callback=data.word.showExtended,
			help="print out extended results (includes things like \"to\" and \"der/die/das\")"
		)
		
		(options, args) = parser.parse_args()
