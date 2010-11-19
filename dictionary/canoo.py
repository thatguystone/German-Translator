from app.mysql import mysql
from app import word

import time

def go():
	db = mysql()

	query = """
		SELECT `de` FROM `translations`
		WHERE
			`pos`="verb"
			AND
			LENGTH(REPLACE(`de`, " ", "")) > (LENGTH(`de`) - 1)
			AND
			LOCATE("...", `de`) = 0
			AND
			LOCATE('"', `de`) = 0
		GROUP BY `de`
	"""
	verbs = db.query(query)
	
	#get a list of all the verbs that don't have adjectives / nouns in their forms
	i = 0
	for v in verbs:
		print "Canoo (%d - %f): %s" % (i, time.time(), v["de"])
		i += 1
		tmp = word.word(v["de"])
		#force the verb to hit canoo
		tmp.isVerb()
	
	#add to the searches table (with provider=canoo, success=0) for anything else
	query = """
		SELECT `de` FROM `translations`
		WHERE
			`pos`!="verb"
			AND
			LENGTH(REPLACE(`de`, " ", "")) > (LENGTH(`de`) - 1)
			AND
			LOCATE("...", `de`) = 0
			AND
			LOCATE('"', `de`) = 0
		GROUP BY `de`
	"""
	others = db.query(query)
	
	for o in others:
		query = """
			INSERT IGNORE INTO `searches`
			SET
				`search`=%s,
				`source`="canoo",
				`success`=0
			;
		"""
		db.insert(query, (o["de"]))
