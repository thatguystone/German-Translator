<?php
#
# This file is part of Verbinator.
# 
# Verbinator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# Verbinator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Verbinator.  If not, see <http://www.gnu.org/licenses/>.
#
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
