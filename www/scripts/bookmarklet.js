javascript:(
	function(){
		var addjQuery;
		addjQuery=document.createElement('script');
		addjQuery.type='text/javascript';
		addjQuery.src='http://ajax.googleapis.com/ajax/libs/jquery/1.4.3/jquery.min.js';
		document.getElementsByTagName('head')[0].appendChild(addjQuery);
		
		addjQuery.onload = function() {
			var bookmarklet;
			bookmarklet=document.createElement('script');
			bookmarklet.type='text/javascript';
			bookmarklet.language='javascript';
			bookmarklet.src='http://deutsch/scripts/bookmarklet.select.js';
			document.getElementsByTagName('head')[0].appendChild(bookmarklet);
			
			css=document.createElement('link');
			css.type='text/css';
			css.rel='stylesheet';
			css.href='http://deutsch/css/bookmarklet.css';
			document.getElementsByTagName('head')[0].appendChild(css);
			
			bookmarklet.onload = function() {
				verbinatorBookmarkletInit();
			}
		}
	}
)();
