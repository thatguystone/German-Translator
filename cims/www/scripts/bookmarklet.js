javascript:(
	function(){
		var css;
		css=document.createElement('link');
		css.type='text/css';
		css.rel='stylesheet';
		css.href='http://cs.nyu.edu/~abs407/deutsch/css/bookmarklet.css';
		document.getElementsByTagName('head')[0].appendChild(css);
		
		var addLabJs;
		addLabJs=document.createElement('script');
		addLabJs.type='text/javascript';
		addLabJs.src='http://cs.nyu.edu/~abs407/deutsch/scripts/LAB.js';
		document.getElementsByTagName('head')[0].appendChild(addLabJs);
		
		addLabJs.onload = function() {
			$LAB
			.script("http://ajax.googleapis.com/ajax/libs/jquery/1.4.3/jquery.min.js").wait()
			.script("https://ajax.googleapis.com/ajax/libs/jqueryui/1.8.6/jquery-ui.min.js").wait()
			.script("http://cs.nyu.edu/~abs407/deutsch/scripts/bookmarklet.select.js")
			.wait(function() {
				verbinatorBookmarkletInit();
				
				//handle frames
				if (window.frames.length > 0) {
					for (i = 0; i < window.frames.length; i++) {
						//fake load the bookmarklet in them
						window.frames[i].location.href = "javascript:(function() {var verbinatorBookmarklet;verbinatorBookmarklet=document.createElement('script');verbinatorBookmarklet.type='text/javascript';verbinatorBookmarklet.src='http://cs.nyu.edu/~abs407/deutsch/scripts/bookmarklet.js';document.getElementsByTagName('head')[0].appendChild(verbinatorBookmarklet);})();";
					}
				}
			});
		}
	}
)();
