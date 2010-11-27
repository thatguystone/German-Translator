# -*- coding: utf-8 -*-
from app.mysql import mysql
from app import utf8
import re
import os
import threading

class wordContainer(object):
	cleanupWords = [
		#words that just need spaces to be removed
		"der", "die", "das", "zu", "to", "zur", "zum", "sich", "oneself",
		
		#words that should always be removed
		"sth.", "etw.", "jmdm.", "jmdn.", "jmds.", "so.", "adj.",
		"jdn.", "jdm.", "sb.",
		
		#funner words
		"bis", "durch", "entlang", u"für", "gegen", "ohne", "um", "aus", "ausser",
		u"außer", "bei", "beim", u"gegenüber", "mit", "nach", "seit", "von", "zu",
		"an", "auf", "hinter", "in", "neben", u"über", "unter", "vor", "zwischen",
		"statt", "anstatt", "ausserhalb", u"außerhalb", "trotz", u"während", "wegen"
	]
	
	#words that indicate we should not include a word in the translation
	verboten = (
		"I ", "he/she/it", "I/he/she/it", "you ", "he/she", "we/they",
		"ich ", "ich/er/sie", "er/sie/es", "ich/er/sie/es", "du ", "er/sie", "wir/sie"
	)

	def __init__(self, word):
		self.word = self.__cleanWord(word)
		self.orig = word
	
	@classmethod
	def pos(cls, en, de):
		#see if we have a modal
		if ((de.word.find("{adj}") == -1 and de.word.find("{vt}") == -1 and de.word.find("{vi}") == -1)
			and de.word in (u"mögen", "wollen", "sollen", "werden", u"können", u"müssen")
		):
			pos = "verb"
		elif (en.orig.find("to ") == 0):
			pos = "verb"
		elif (de.orig.find("{m}") >= 0 or de.orig.find("{f}") >= 0 or de.orig.find("{n}") >= 0 or de.orig.find("{pl}") >= 0):
			pos = "noun"
		else:
			pos = "adjadv"
		
		return pos
	
	@classmethod
	def setup(cls):
		#what the sum should equal in order to have none of the words in it
		cls.lenVerboten = len(cls.verboten) * -1
	
	def __cleanWord(self, word):
		word = re.sub(r'(\(.*\))', "", word)
		word = re.sub(r'(\[.*\])', "", word)
		word = re.sub(r'(\{.*\})', "", word)
		word = re.sub(r'(\\.*\\)', "", word)
		word = re.sub(r'(\/.*\/)', "", word)
		
		word = word.replace("\"", "").replace("\'", "").strip()
		
		#remove extra words from the definition
		words = word.split(" ")
		
		#build up a new word that fits our parameters
		#easier to do this than remove words from the list
		newWord = []
		
		if (len(words) == 1):
			newWord.append(words[0])
		else:
			for w in words:
				if (len(w.strip()) > 0 and not w in wordContainer.cleanupWords):
					newWord.append(w)
			
		word = " ".join(newWord)
		
		return word

	def isUsableWord(self):
		if (sum([self.word.find(i) for i in wordContainer.verboten]) != wordContainer.lenVerboten):
			return False
		
		return True
	
	#for debug printing
	def __repr__(self):
		return str(self.word.encode("utf-8"))

class lineThread(threading.Thread):
	def setup(self, sema):
		self.sema = sema
		self.db = mysql()
	
	def run(self):
		while True:
			line = getLine(self.sema)
			if (line == False):
				break
			self.parseLine(line)
	
	def parseLine(self, line):
		#"::" is the de-en separator
		#"|" is the word separator
		#and then strip the spaces from the words
		(de, en) = [[
			word.strip()
			for word in part.split("|")]
			for part in line.split("::")[0:2]
		]
		
		for e, d in zip(en, de):
			e = self.cleanLine(e).split(";")
			d = self.cleanLine(d).split(";")
			
			tmpInnerEn = []
			for w in e:
				w = wordContainer(w)
				if (w.isUsableWord()):
					tmpInnerEn.append(w)
			
			tmpInnerDe = []
			for w in d:
				w = wordContainer(w)
				if (w.isUsableWord()):
					tmpInnerDe.append(w)
			
			if (len(tmpInnerDe) != 0 and len(tmpInnerEn) != 0):
				for e in tmpInnerEn:
					for d in tmpInnerDe:
						if (d.word != "" and e.word != ""):
							self.db.insert("""
								INSERT IGNORE INTO `translations`
								SET
									`en`=%s,
									`de`=%s,
									`enExt`=%s,
									`deExt`=%s,
									`pos`=%s
								;
							""", (
								e.word,
								d.word,
								e.orig,
								d.orig,
								wordContainer.pos(e, d)
								)
							)

	#chemnitz did some bad formatting with their output
	def cleanLine(self, line):
		line = re.sub(r'(\{.*;.*\})', "", line)
		line = re.sub(r'(\(.*;.*\))', "", line)
		line = line.strip()
		return line
	
def go(args):
	if (len(args) == 0):
		print "Specify a dictionary file."
		return
	elif (not os.path.exists(args[0])):
		print "The input path could not be found."
		return
	
	wordContainer.setup()
	
	global dic
	dic = open(args[0], "r")
	
	#start 4 threads to deal with all the data
	sema = threading.Semaphore()
	for i in range(0, 4):
		t = lineThread()
		t.setup(sema)
		t.start()
	
	
def getLine(sema):
	sema.acquire()
	line = utf8.encode(dic.readline().strip())
	sema.release()
	
	if (line == ""):
		return False
	
	return line
