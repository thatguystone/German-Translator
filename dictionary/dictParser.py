from app.mysql import mysql

def parseLine(line):
	#don't look at verb forms
	if (line.find("I/he/she") > -1):
		return
	
	#"::" is the de-en separator
	#"|" is the word separator
	#and then strip the spaces from the words
	(de, en) = [[
		word.strip()
		for word in part.split("|")]
		for part in line.split("::")
	]
	
	for e, d in zip(en, de):
		enW = e.split(";")
		for w in enW:
			cleanWord(enW)
		
		deW = d.split(";")
	
	print "----------"

def cleanWord(word):
	word = re.sub(r'(\[.*\])', "", word)
	return word

def go():
	dic = open("dictionary/de.txt", "r")
	
	for line in dic:
		parseLine(line)
