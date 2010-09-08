#if we should print extended information about the translations
extended = False

def showExtended(option, opt, value, parser):
	"""Switches the display of extended information about the translations on"""
	
	global extended
	extended = True

#adapted from: http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/
def printTable(table):
	"""Given a list of dictionaries, prints out a nice table of it all"""
	
	enKey = 'en-ext' if extended else 'en'
	deKey = 'de-ext' if extended else 'de'
	
	colWidths = dict()
	
	#put in our headers for width calculations
	table.insert(0, {
		'en': 'English',
		'en-ext': 'English',
		'de': 'Deutsch',
		'de-ext': 'Deutsch'
	})
	
	#i'm assuming that each dictionary has the same keys
	for col in table[0].keys():
		colWidths[col] = max([len(unicode(row[col])) for row in table])
	
	#remove the headers
	table.pop(0)
	
	#print the headers, in the center of the column
	print "English".center(colWidths[enKey] + 2), "Deutsch".center(colWidths[deKey])
	
	#print the results
	for row in table:
		print row[enKey].ljust(colWidths[enKey] + 2), row[deKey].ljust(colWidths[deKey])
	
def showResults(word, results):
	"""Prints out some nice stuff for the translations"""
	
	print "Searched word: %s" % word, "\n"
	printTable(results)
