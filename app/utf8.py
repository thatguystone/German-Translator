def encode(s):
	ret = s
	if (type(s) != unicode):
		ret = unicode(s, "utf-8")
	
	return ret
