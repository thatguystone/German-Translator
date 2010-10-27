var punctuation = [".", ",", ":", ";", "?", "!"];
var mouseStart = {x: 0, y: 0};
var mouseStop = {x: 0, y: 0};

$(function() {
	
	$("body").bind("mousedown", function(e) {
		mouseStart.x = e.clientX;
		mouseStart.y = e.clientY;
	});
	
	$("body").bind("mouseup", function(e) {
		mouseStop.x = e.clientX;
		mouseStop.y = e.clientY;
		
		text = getSelectedText();
		
		selectedText = text;
		
		translate(text);
		return;
		
		allText = $(text.focusNode.parentNode);
		//are we trying to translate just a single word?
		if (selectedText.indexOf(" ") == -1)
			translate(selectedText);

		//nope, we're translating a clause
		else
			translateClause(selectedText, allText);
	});
	
	$("#translationBox").click(function() {
		$(this).hide();
	})
	
	$("#translationBox").css("left", ($(window).width() - $("#translationBox").outerWidth() - 10) + "px");
});

function translate(text) {
	if (text.toString().length == 0)
		return;
	
	text = text.toString()
	
	$("#translationBox").addClass("loading").find(".container").hide().end().show();
	$("#translations").empty();
	$("#highlightedText").text(text);
	
	$.ajax({
		url: "http://deutsch/api",
		type: "get",
		dataType: "jsonp",
		data: "input=" + text.toString(),
		success: function(data) {
			var table = $("#translations");
			
			if (data.length == 0) {
				table.append('<tr><td colspan="2">No translations found.</td></tr>');
			} else {
				$.each(data, function(i, v) {
					table.append("<tr><td>" + v.en + "</td><td>" + v.de + "</td></tr>");
				});
			}
			
			$("#translationBox .container").show();
			height = ($("#translationBox .title").height() + $("#translationBox .translation").height()) + 14; 
			$("#translationBox").removeClass("loading").css("height", height + "px");
			$("#translationBox .container").css("height", (height - 2) + "px");
		}
	});
}

function translateClause(selectedText, $text) {
	parentText = $text.text();
	start = parentText.indexOf(selectedText);
	
	loc = findPunc(selectedText);
	if (loc[1] != -1) {
		//we found some punctuation in the text; let's see where it is
		
		selectedPunc = selectedText.length - loc[1]
		parentStart = start + selectedPunc;
		if (selectedPunc > loc[1]) { //the majority of the text is to the left of the punctuation
			console.log("before -- " + parentStart);
			startLoc = findPunc(parentText, parentStart, -1);
			text = parentText.substring(startLoc, parentStart);
		} else { //the majority is to the right
			console.log("after");
			endLoc = findPunc(parentText, parentStart, 1);
			text = parentText.substring(parentStart, endLoc);
		}
		
		console.log(text);
	}
}

/**
 * start - where in the string to being the search
 * direction - left (-) or right (+)
 */
function findPunc(text, start, direction) {
	if (!start)
		start = 0
	if (!direction)
		direction = 1

	punc = "";
	loc = -1;
	/*for each (p in punctuation) {
		if (direction > 0)
			loc = text.indexOf(p, start);
		else
			loc = text.lastIndexOf(p, start);
		
		if (loc != -1) {
			punc = p
			break 
		}
	}*/
	
	return [punc, loc]
}

/**
 * $text - the text element that was highlighted
 * direction - left (-) or right (+)
 */
function searchMore($text, direction) {
	more = "";
	origText = $text.text()
	
	console.log("OrigText: " + origText);
	console.log("Direction: " + direction);
	
	start = 0
	end = origText.length
	newText = ""
	
	found = false
	while (!found) {
		//get the parent and find our original text in him
		$text = $text.parent();
		newText = $text.text();
		
		//the location of the start of the original text in the parent text
		start = newText.indexOf(origText);
		
		console.log("NewText (" + start + "): " + newText);
		
		//find out if we have punctuation in the parent text
		loc = findPunc(newText, start, direction);
		
		//did we find some punctuation in that search?
		if (loc != -1 || $text == document) {
			start = loc[1];
			end = start + end;
			found = true;
		}
	}
	
	console.log("Start: " + start + "; End: " + end);
	
	return newText.substring(start, end);
}

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
