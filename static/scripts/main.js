var $translations, $query, $table, $searchPhrase;

var colors = [
	"FFCBAD", "FFD876", "D8E9BF", "C5D6CC", "D7BBD9", "B9FCC1"
];

$(function() {
	$translations = $(".translations");
	$query = $("#query");
	$table = $("#translations");
	$searchPhrase = $("#searchPhrase");

	$("#translationInputs").submit(function() {
		search($query.val(), false);
		return false;
	});

	$("#darkMagic").click(function() {
		search($query.val(), true);
		return false;
	});

	$('#bookmarkletQuestion').qtip({
		content: "When you're on a German site and wish you had some verb \
			translations handy, this is what you want.<br><br>Simply drag the \
			bookmarklet to the left to your bookmarks toolbar, and whenever you're \
			on a German website, click the bookmarklet to activate the translator; then \
			all you have to do it highlight text, and you'll get instant translations.<br><br> \
			Click the link for an example of how to create the bookmarklet.",
		style: 'light'
	});


	//get the query from the url
	query = document.location.pathname.substring(1);

	//if we have a query...
	if (query.length > 0) {
		//and run our search
		search(query);
	}

	$query.focus();
});

var running = false;
var tries = 0;

function getDictLink(word) {
	return "<a href=\"http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=&search=" + encodeURI(word) + "\" target=\"_blank\">" + $('<div/>').text(word).html() + "</a>";
}

function search(query, darkMagic) {
	if (running) {
		triedSearch();
		return;
	}

	//clean out all the tags -- thanks jQuery!
	//throw it into a <div> so that all the text (even that outside of tags) is returned
	query = $("<div>" + unescape(query) + "</div>").text().trim();

	//remove all double spaces -- keep consistent with the backend
	while (query.indexOf("  ") > -1)
		query = query.replace("  ", " ");

	query = trim(query, ",.-—?!").trim();

	//set the value of the search box
	$query.val(query);

	running = true;

	var highlighted = query.replace("-", "").replace("—", " ").split(" ");

	$.ajax({
		url: "/api",
		type: "get",
		data: {"input": query, "aggressive": (darkMagic ? "1" : "0")},
		dataType: "json",
		beforeSend: function() {
			$translations.addClass("loading");
			$table.empty();
			$searchPhrase.empty();
		},
		success: function(data) {
			if (typeof data.length == "undefined" || data.length == 0) {
				$table.append('<tr><td colspan="2">No translations found.</td></tr>');
			} else {
				var currentColor = -1;
				var currentWord = -1;
				var style = "";

				//make the translations print out in sentence order
				data.sort(dataSorter);
				//randomize the highlight colors
				colors.shuffle();

				$.each(data, function(i, v) {
					if (currentWord == -1 || v.deWordLocation != currentWord) {
						currentWord = v.deWordLocation;
						currentColor = (currentColor + 1) % colors.length;

						style = "style=\"background-color: #" + colors[currentColor] + ";\"";

						highlighted[currentWord] = "<span " + style + ">" + highlighted[currentWord] + "</span>";
					}

					orig = ""
					if (typeof v.deOrig != "undefined")
						orig = "(" + getDictLink(v.deOrig) + ")";

					$table.append("<tr " + style + "><td>" + v.en + "</td><td>" + getDictLink(v.de) + " " + orig + "</td></tr>");
				});

				$searchPhrase.html(highlighted.join(" "));
			}

			$translations.removeClass("loading");

			//reset our state
			tries = 0;
			running = false;
		}
	});
}

function dataSorter(a, b) {
	if (a.deWordLocation < b.deWordLocation)
		return -1;
	if (a.deWordLocation == b.deWordLocation)
		return 0;

	return 1;
}

Array.prototype.shuffle = function() {
 	var len = this.length;
	var i = len;
	 while (i--) {
	 	var p = parseInt(Math.random()*len);
		var t = this[i];
  	this[i] = this[p];
  	this[p] = t;
 	}
};

function triedSearch() {
	tries++;
	if (tries >= 3) {
		alert("Calm down.  The translation is going.  Give it some time.");
	}
}

function trim(s, chars) {
	return rtrim(ltrim(s, chars), chars);
}

function ltrim(s, chars) {
	var l=0;
	while(l < s.length && chars.indexOf(s[l]) > -1)
		l++;
	return s.substring(l, s.length);
}

function rtrim(s, chars) {
	var r=s.length -1;
	while(r > 0 && chars.indexOf(s[r]) > -1)
		r-=1;
	return s.substring(0, r+1);
}
