<?php

ini_set('display_errors', true);
ini_set('display_startup_errors', true);
error_reporting(E_ALL);

//this is just a quick router for pages -- it does nothing special

//get the page they're requesting
$file = (isset($_GET['requestPath']) ? $_GET['requestPath'] : "index");

//clean up its name
$file = preg_replace('/[^a-z]*/i', '', $file);

//see if we have that file
if (!file_exists('../pages/'.$file.'.html'))
	$file = 'index';

$file = '../pages/'.$file.'.html';

require('../pages/pages.header.tmpl');
require($file);
require('../pages/pages.footer.tmpl');
