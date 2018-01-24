$(document).ready(function(){
	if ($(window).width() > 768) {
		$('.add').addClass('drag');
		$(".drag").draggable({
		  containment: "window"
		});
	}
	$('.post-href').click(function() {
		var number = $(this).attr('href');
		var addition = '>>';
		if ($('textarea').val() != '') {addition = '\n>>'};		
		var new_val = $('textarea').val() + addition + number.substring(1, number.length) + '\n';
		$('textarea').val(new_val);
		if (!$('.add').hasClass('drag')) {
			 //$('.add').get(0).focus();
			$('html,body').animate({
				scrollTop: $('.add').offset().top
			}, 1000);
			return false;
		}
	});
	$(".post-header").each(function(i) {
		++i;
    	$(this).find(".post-number").text(i++);
	});
	$('.date').each(function() {
		$(this).text(localTime($(this).text()));
	});
	$(window).on('resize', function(){
		var win = $(this); //this = window
		if ($(window).width() > 768) {
			$('.add').addClass('drag');
			$(".drag").draggable({
			  containment: "window"
			});
		}
		if (win.width() <= 768) {
			$('.add').removeClass('drag')
		}
		if (win.width() <= 480) {
			 $(form).hide();
		}
	});
	$('body').on('mouseover', 'a.reply', function() {
		var display = $($(this).attr('href')).clone();
		display.toggleClass('to_die', true);
		display.css({
			 display:'inline',
			 position: 'absolute',
			 top: $(this).offset().top - $(this).height()/2,
			 left: $(this).offset().left + $(this).width(),
			 border: '1px black solid',
			 zIndex: 1000,
			 background: 'white'
		});
		$('body').append(display);
	});
	$('body').on('mouseleave', 'a.reply', function(e) {
		$('.to_die').remove();
	});
	/*
	$('body').on('mouseleave', 'a.reply', function(e) {
		setTimeout(function() {
			if (!$(e.relatedTarget).parents('.to_die').length) {
				console.log($(e.relatedTarget).parents('.to_die').length);
				$('.to_die').remove();
			}
		}, 1000);
	});*/
});

function die() {
	 
}

function localTime(utc) {
	utc = utc + ' UTC';
	var month = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
	var d = new Date(utc);
	var date = d.getDate() + '-' + month[d.getMonth()] + '-' + d.getFullYear();
	var time = d.toLocaleTimeString(navigator.languages[0]);
	return date + ' ' + time
}
