#if we should print extended information about the translations
extended = False

def showExtended(option, opt, value, parser):
	"""Switches the display of extended information about the translations on"""
	
	global extended
	extended = True

#adapted from: http://ginstrom.com/scribbles/2007/09/04/pretty-printing-a-table-in-python/
def printTable(table):
	"""Given a list of dictionaries, prints out a nice table of it all"""
	
	colWidths = dict()
	
	#i'm assuming that each dictionary has the same keys
	for col in ["en", "de"]:
		colWidths[col] = max([len(row[col]) for row in table])
	
	#cheap hack...meh...this isn't going to be used for long anyway
	if (colWidths["en"] < 7):
		colWidths["en"] = 7
	if (colWidths["de"] < 7):
		colWidths["de"] = 7
	
	#print the headers, in the center of the column
	print "English".center(colWidths["en"] + 2), "Deutsch".center(colWidths["de"])
	
	#print the results
	for row in table:
		print row["en"].ljust(colWidths["en"] + 2), row["de"].ljust(colWidths["de"]),
		if ("deOrig" in row):
			print "(" + row["deOrig"] + ")",
		print

import types
def showResults(word, results):
	"""Prints out some nice stuff for the translations"""
	
	print "Searched word: %s" % word, "\n"
	
	if (type(results) == types.NoneType or len(results) == 0):
		print "There were no words found"
	else:
		printTable(results)
