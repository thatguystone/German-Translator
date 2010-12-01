var colors = [
	"FFCBAD", "FFD876", "D8E9BF", "C5D6CC", "D7BBD9", "B9FCC1"
];

var $title, $translationBox, $translations, $highlightedText, $translationBoxContainer, $translationsDiv;
var windowHeight, windowWidth;

function verbinatorBookmarkletInit() {
	//stop the bookmarklet from being loaded multiple times -- this probably should be in the bookmarklet loader, but meh
	if ($("#translationBox").length > 0) {
		return;
	}

	$("body").append('<div id="translationBox"> \
		<div class="container"> \
			<div class="title"> \
				<span class="fixed">Translation for:</span> <span id="highlightedText">test</translation> \
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
	$highlightedText = $("#highlightedText");
	$translationBoxContainer = $("#translationBox .container");
	
	windowWidth = $(window).width();
	windowHeight = $(window).height();
	
	$("body").bind("mouseup", function(e) {
		text = getSelectedText();
		selectedText = text;
		translate(text);
	});

	$translationBox.css("left", (windowWidth - $translationBox.outerWidth() - 10) + "px");
}

function translationBoxBind() {
	$translationBox.click(function() {
		$(this).hide();
	});
}

function translationBoxUnbind() {
	$translationBox.unbind("click");
}

function translate(text) {
	text = text.toString().trim();
	
	if (text.length == 0)
		return;
	
	$translationBox.addClass("loading").find(".container").hide().end().show();
	$translations.empty();
	$highlightedText.text("loading...");
	//don't let the translation box be closed during loading
	translationBoxUnbind();
	$translationBox.css("height", "35px");
	
	var highlighted = text.replace("-", "").split(" ");
	
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
				
			if (data.length == 0) {
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
						orig = "(" + v.deOrig + ")";
					
					$table.append("<tr " + style + "><td>" + v.en + "</td><td>" + v.de + " " + orig + "</td></tr>");
				});
				
				$highlightedText.html(highlighted.join(" "));
			}
			
			$translationBoxContainer.show();
			
			//allow the box to be closed by clicking it
			translationBoxBind();
			
			//use the calculated height for our measurements, not the css height
			height = $translationsDiv.height() + 15; //magic 15! no, it's for the padding / borders
			titleHeight = $title.height();
			
			if ((titleHeight + height) > windowHeight)
				height = windowHeight - titleHeight - 30; //fit the popup into the window
			
			$translationsDiv.css("height", (height - 15) + "px");
			$translationBox.removeClass("loading").css("height", (titleHeight + height) + "px");
			$translationBoxContainer.css("height", (titleHeight + height - 2) + "px");
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
