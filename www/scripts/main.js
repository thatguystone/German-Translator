var $translations, $query, $table, $searchPhrase;

var colors = [
	"F7977A", "FFF79A", "C4DF9B", "6ECFF6", "8882BE", "BC8DBF", "F6989D",
	"F9AD81", "82CA9D", "8493CA", "D7D7D7"
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
	query = $("<div>" + unescape(query) + "</div>").text();
	
	//set the value of the search box
	$query.val(query);
	
	running = true;
	
	var highlighted = query.split(" ");
	
	$.ajax({
		url: "/api/",
		type: "get",
		data: {"input": query},
		dataType: "json",
		beforeSend: function() {
			$translations.addClass("loading");
			$table.empty();
		},
		success: function(data) {
			if (data.length == 0) {
				$table.append('<tr><td colspan="2">No translations found.</td></tr>');
			} else {
				var currentColor = -1;
				var currentWord = -1;
				var style = "";
				
				$.each(data, function(i, v) {
					if (currentWord == -1 || v.deWordLocation != currentWord) {
						currentWord = v.deWordLocation;
						currentColor = (currentColor + 1) % colors.length;
						
						style = "style=\"background: #" + colors[currentColor] + ";\"";
						
						highlighted[currentWord] = "<span " + style + ">" + highlighted[currentWord] + "</span>";
					}
					
					$table.append("<tr " + style + "><td>" + v.en + "</td><td>" + v.de + "</td></tr>");
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

function triedSearch() {
	tries++;
	if (tries >= 3) {
		alert("Calm down.  The translation is going.  Give it some time.");
	}
}
