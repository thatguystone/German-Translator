from optparse import OptionParser

class router:
	"""Provides a means of getting the word to be translated from the user"""
	
	def go(self):
		"""Routes the command through the application"""
		
		(opts, args) = self.setupOptions()
		
		if (opts.buildDict):
			from dictionary import dictParser
			dictParser.go(args)
			
			from dictionary import woxikon
			woxikon.go()
		else:
			from app import translator
			import displayer
			
			if (opts.word == None):
				word = raw_input("Enter the word to translate: ")
			else:
				word = opts.word
			
			translator.beAggressive = opts.aggressive
			
			displayer.showResults(word, translator.translate(word))
		
	def setupOptions(self):
		"""Contains the command line option parser"""
		
		parser = OptionParser()
		
		parser.add_option("-a", "--aggressive",
			action="store_true", default=False, dest="aggressive",
			help="be aggressive about which verbs are thrown out"
		)
		
		parser.add_option("-w", "--word",
			action="store", type="string", dest="word",
			help="the word to translate (if not entered, will prompt)"
		)
		
		parser.add_option("-d", "--build-dictionary",
			action="store_true", default=False, dest="buildDict",
			help="if the dictionary should be built"
		)
		
		return parser.parse_args()
