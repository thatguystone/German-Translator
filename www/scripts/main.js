var $translations, $query, $table;

$(function() {
	$translations = $(".translations");
	$query = $("#query");
	$table = $("#translations");

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
				$.each(data, function(i, v) {
					$table.append("<tr><td>" + v.en + "</td><td>" + v.de + "</td></tr>");
				});
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
