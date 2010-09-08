#adapted from: http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/
def printTable(table):
	colWidths = dict()
	
	#put in our headers for width calculations
	table.insert(0, {'en': 'English', 'de': 'Deutsch'})
	
	#i'm assuming that each dictionary has the same keys
	for col in table[0].keys():
		colWidths[col] = max([len(unicode(row[col])) for row in table])
	
	#remove the headers
	table.pop(0)
	
	#print the headers, in the center of the column
	print "English".center(colWidths['en'] + 2), "Deutsch".center(colWidths['de'])
	
	#print the results
	for row in table:
		print row['en'].ljust(colWidths['en'] + 2), row['de'].ljust(colWidths['de'])
	
def showResults(word, results):
	print "Searched word: %s" % word, "\n"
	printTable(results)
