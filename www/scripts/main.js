var $translations, $query, $table, $searchPhrase;

var colors = [
	"FFCBAD", "FFF9B6", "D8E9BF", "C5D6CC", "D7BBD9", "B9FCC1" 
];

$(function() {
	$translations = $(".translations");
	$query = $("#query");
	$table = $("#translations");
	$searchPhrase = $("#searchPhrase");

	$("#translationInputs").submit(function() {
		search($query.val());
		return false;
	});
	
	//get the query from the url
	query = document.location.pathname.substring(1);
	
	//if we have a query...
	if (query.length > 0) {
		//and run our search
		search(query);
	}
});

var running = false;
var tries = 0;

function search(query) {
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
	
	//set the value of the search box
	$query.val(query);
	
	running = true;
	
	var highlighted = query.replace("-", "").split(" ");
	
	$.ajax({
		url: "/api/",
		type: "get",
		data: {"input": query},
		dataType: "json",
		beforeSend: function() {
			$translations.addClass("loading");
			$table.empty();
			$searchPhrase.empty();
		},
		success: function(data) {
			if (data.length == 0) {
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
					
					$table.append("<tr " + style + "><td>" + v.en + "</td><td>" + v.de + " (" + v.deOrig + ")</td></tr>");
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
