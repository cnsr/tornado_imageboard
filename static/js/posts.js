$(document).ready(function(){
	$(".add").draggable({
	  containment: "window"
	});
	$('.post-href').click(function() {
		var number = $(this).attr('href');
		var addition = '>>';
		if ($('textarea').val() != '') {addition = '\n>>'};		
		var new_val = $('textarea').val() + addition + number.substring(1, number.length) + '\n';
		$('textarea').val(new_val);
	});
	$(".post-header").each(function(i) {
		++i;
    	$(this).find(".post-number").text(i++);
	});
});
