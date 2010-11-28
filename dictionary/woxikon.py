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
			AND
			LOCATE('/', `de`) = 0
		GROUP BY `de`
	"""
	verbs = db.query(query)
	
	#get a list of all the verbs that don't have adjectives / nouns in their forms
	i = 0
	for v in verbs:
		print "Woxikon (%d - %f): %s" % (i, time.time(), v["de"])
		i += 1
		tmp = word.word(v["de"].lower())
		tmp.verb.scrapeWoxikon()

	#add to the searches table (with provider=canoo, success=0) for anything else
	query = """
		INSERT IGNORE INTO `searches` (`search`, `source`, `success`)
		SELECT `de`, "canoo", "0" FROM `translations`
		WHERE
			`pos`!="verb"
			AND
			LENGTH(REPLACE(`de`, " ", "")) > (LENGTH(`de`) - 1)
			AND
			LOCATE("...", `de`) = 0
			AND
			LOCATE('"', `de`) = 0
			AND
			LOCATE('/', `de`) = 0
		GROUP BY `de`
	"""
	db.insert(query)
