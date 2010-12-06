var colors = [
	"FFCBAD", "FFD876", "D8E9BF", "C5D6CC", "D7BBD9", "B9FCC1"
];

var $title, $translationBox, $translations, $highlightedText, $translationBoxContainer, $translationsDiv, $translationsTable;
function verbinatorBookmarkletInit() {
	//stop the bookmarklet from being loaded multiple times -- this probably should be in the bookmarklet loader, but meh
	if ($("#translationBox").length > 0) {
		return;
	}

	$("body").append('<div id="translationBox"> \
		<div class="container"> \
			<div class="windowTitle"> \
				Verbinator Translations \
				<img src="http://deutsch/images/close.png" id="closeVerbinatorWindow" /> \
			</div> \
			<div class="title"> \
				<span class="fixed">Translation for:</span> <span id="highlightedText">Loading...</span> \
			</div> \
			<div class="translation"> \
				<table class="info"> \
					<tr> \
						<th>English</th> \
						<th>Deutsch</th> \
					</tr> \
					<tbody id="translations"> \
					</tbody> \
				</table> \
			</div> \
		</div> \
	</div>');
	
	$title = $("#translationBox .title");
	$translationBox = $("#translationBox");
	$translations = $("#translations");
	$translationsDiv = $("#translationBox .container .translation");
	$windowTitle = $("#translationBox .container .windowTitle");
	$translationsTable = $translationsDiv.find(".info");
	$highlightedText = $("#highlightedText");
	$translationBoxContainer = $("#translationBox .container");
	
	$("body").bind("mouseup", function(e) {
		text = getSelectedText();
		selectedText = text;
		translate(text);
	});
	
	$("#closeVerbinatorWindow").click(function() {
		$translationBox.hide();
		$highlightedText.text("");
	});
	
	$translationBox.draggable({
		handle: ".container .windowTitle"
	}).disableSelection();
}

function getDictLink(word) {
	return "<a href=\"http://dict.leo.org/ende?lp=ende&lang=de&searchLoc=0&cmpType=relaxed&sectHdr=on&spellToler=&search=" + encodeURI(word) + "\" target=\"_blank\">" + $('<div/>').text(word).html() + "</a>";
}

function translate(text) {
	text = text.toString().trim();
	
	if (text.length == 0 || text == $highlightedText.text())
		return;
	
	//adapt to the window width as it changes
	$translationBox.css("left", ($(window).width() - $translationBox.outerWidth() - 10) + "px").css("top", "10px");
	
	//show that window
	$translationBox.addClass("loading").find(".container").hide().end().show();
	$translations.empty();
	$highlightedText.text("loading...");
	//don't let the translation box be closed during loading
	$translationBox.css("height", "35px");
	
	var highlighted = trim(text.replace("-", "").replace("—", " "), ",.-—?!").trim().split(" ");
	
	$.ajax({
		url: "http://deutsch/api",
		type: "get",
		dataType: "jsonp",
		data: "input=" + encodeURIComponent(text.toString()),
		success: function(data) {
			var $table = $("#translations");
			var currentColor = -1;
			var currentWord = -1;
			var style = "";
			
			if (data.length == 0 || !data.sort) {
				$table.append('<tr><td colspan="2">No translations found.</td></tr>');
				$highlightedText.text("No translations found.");
			} else {
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
				
				$highlightedText.html(highlighted.join(" "));
			}
			
			$translationBoxContainer.show();
			
			//adapt to the window height as it changes
			windowHeight = $(window).height();
			titleHeight = $title.height();
			windowTitleHeight = $windowTitle.height();
			
			//make the window as large as it can -- we need to calculate the height of the window without scroll bars
			//--if there are going to be scroll bars at max height, then we calculate the height with the scroll bars
			//  intact.  otherwise, scroll bars appear sometimes, and they throw off the height calculation when they
			//  force some translations to new lines.  So, this just makes sure that the window sizes properly.
			$translationsDiv.css("height", (windowHeight - titleHeight - 15) + "px");
			$translationBox.removeClass("loading").css("height", (windowHeight) + "px");
			$translationBoxContainer.css("height", (windowHeight - 1) + "px");
			
			//use the calculated height for our measurements, not the css height
			height = $translationsTable.height() + 15; //magic 15! no, it's for the padding / borders
			
			if ((titleHeight + height) > windowHeight)
				height = windowHeight - titleHeight - windowTitleHeight - 30; //fit the popup into the window
			
			$translationsDiv.css("height", (height - 15) + "px");
			$translationBox.css("height", (titleHeight + windowTitleHeight + height + 2) + "px");
			$translationBoxContainer.css("height", (titleHeight + height + windowTitleHeight) + "px");
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

function getSelectedText(){
	var t = '';
	if (window.getSelection)
		t = window.getSelection();
	else if (document.getSelection)
		t = document.getSelection();
	else if (document.selection)
		t = document.selection.createRange().text;
	return t;
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
