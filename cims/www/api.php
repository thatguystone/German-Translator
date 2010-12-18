<?php
//load up the config for which server to query
$config = parse_ini_file('/home/abs407/deutsch/config.ini');

//attempt to make a request
$ch = curl_init('http://'.$config['cimsServerHost'].':'.$config['cimsServerPort'].'/?'.$_SERVER['QUERY_STRING']);
curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);

//attempt to execute a single request
$ret = curl_exec($ch);

//if the request failed, try to start the server, and keep trying until we get something!
while (curl_errno($ch) != 0) {
	//PHP isn't that happy...so let's just do a CGI request to the server starter...which does it right
	startServer();
	$ret = curl_exec($ch);
}

//we got something, close that connection and send the output
curl_close($ch);
echo $ret;

/** 
 * Starts the python server which we throw all our requests to.
 */
function startServer() {
	$ch = curl_init('http://cs.nyu.edu/~abs407/cgi-bin/startServer.cgi');
	curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
	curl_exec($ch);
	curl_close($ch);
}
