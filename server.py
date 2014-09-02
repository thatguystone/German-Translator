import bottle
import json
import os
import re
import translator

app = bottle.default_app()
reject = re.compile('[^a-zA-Z0-9]')

app.config.load_dict({
	'debug': False,
	'fcgi': False,
	'fcgi_socket': os.path.dirname(os.path.realpath(__file__)) + '/server.sock',
	'hit_internet': False,
	'static_root': os.path.dirname(os.path.realpath(__file__)) + '/static',
	'database': {
		'host': 'localhost',
		'user': 'root',
		'pass': 'password',
		'db': 'verbinator',
	},
	'word': {
		'verb_start': 4,
		'verb_end': 4,
	},
})
app.config.load_config('config.ini')

@app.route('/')
def index():
	return bottle.static_file('index.html', root=app.config['static_root'])

@app.route('/static/<path:path>')
def index(path):
	return bottle.static_file(path, root=app.config['static_root'])

@app.route('/api')
def api():
	res = json.dumps(translator.translate(
		bottle.request.query.input,
		not not bottle.request.query.aggressive))

	if bottle.request.query.callback:
		bottle.response.content_type = 'application/javascript'
		cb = re.sub(reject, '', bottle.request.query.callback)
		return cb + '(' + res + ');'
	else:
		bottle.response.content_type = 'application/json'
		return res

if app.config['fcgi']:
	app.run(server='flup', bindAddress=None)
else:
	app.run(host='localhost', port=8777, reloader=True)
