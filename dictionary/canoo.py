from app.mysql import mysql

def go():
	db = mysql()

	query = """
		SELECT * FROM `translations`
		WHERE
			`pos`="verb"
			AND
			length(replace(`de`, " ", "")) > (length(`de`) - 2)
		GROUP BY `de`
	"""
	verbs = db.query(query)
	print len(verbs)
	
	#get a list of all the verbs that don't have adjectives / nouns in their forms
	
	#add to the searches table (with provider=canoo, success=0) for any noun / adjadv
