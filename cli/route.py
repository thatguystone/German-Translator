from optparse import OptionParser

class router:
	"""Provides a means of getting the word to be translated from the user"""
	
	def go(self):
		"""Routes the command through the application"""
		
		(opts, args) = self.setupOptions()
		
		if (opts.buildDict):
			from dictionary import dictParser
			dictParser.go(args)
		else:
			from app import translator
			import displayer
			
			if (opts.word == None):
				word = raw_input("Enter the word to translate: ")
			else:
				word = opts.word
			
			displayer.showResults(word, translator.translate(word))
		
	def setupOptions(self):
		"""Contains the command line option parser"""
		
		parser = OptionParser()
		
		#parser.add_option("-e", "--extended-results",
		#	action="callback", callback=translator.word.showExtended,
		#	help="print out extended results (includes things like \"to\" and \"der/die/das\")"
		#)
		
		parser.add_option("-w", "--word",
			action="store", type="string", dest="word",
			help="the word to translate (if not entered, will prompt)"
		)
		
		parser.add_option("-d", "--build-dictionary",
			action="store_true", default=False, dest="buildDict",
			help="if the dictionary should be built"
		)
		
		return parser.parse_args()
