$(document).ready(function(){
	if (localStorage.name != '' && localStorage.name != null) $('#username').val(localStorage.name);
	if ($(window).width() > 768) {
		$('.add').addClass('drag');
		if (typeof nodrag === 'undefined') {
			$(".drag").draggable({
			  containment: "window"
			});
		}
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
	$('#sendpost').on('click', function(){
		if ($('#username').length != 0) localStorage.name = $('#username').val();
	})
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
			 $('form').hide();
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
	$('.report').on('click', function() {
		$('.report-popup').remove();
		var id = $(this).attr('data-id');		
		var popup = "<div class='report-popup' data-id="+id+"><select>"+
			"<option>Spam</option>"+
			"<option>Inapropriate content</option>"+
			"<option>Harassment</option>"+
			"<option>Wow rude</option>"+
			"<option>Other</option>"+
			"</select><button id='close-report'>X</button>"+
			"<button id='submit-report'>Report</button></div>";
		var off_top = $(this).offset()['top'] + 9;
		var off_left= $(this).offset()['left'] + 9;
		$('body').append(popup);
		var pop = $('.report-popup');
		pop.css({
				"position":'relative',
				"background": 'white',
				"border": '1px solid black',
				"z-index": '1000',
				"display": 'inline-block',
				});
		pop.find('#submit-report').css('display', 'block');
		pop.offset({'top': off_top, 'left': off_left});
	});
	$('body').on('click', '#close-report', function(){
		 $('.report-popup').remove();
	});
	$('body').on('click', '#submit-report', function(e){
		e.preventDefault();
		var id = $(this).closest('.report-popup').attr('data-id');
		var reason = $(this).closest('.report-popup').find('select :selected').text();
		sendAjaxReport(id, reason);
		$('.report-popup').remove();
		popUp('Report has been sent!');
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
	//utc = utc + ' UTC';
	var month = ['1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12'];
	var d = new Date(utc);
	var date = d.getDate() + '-' + month[d.getMonth()] + '-' + d.getFullYear();
	var time = d.toLocaleTimeString(navigator.languages[0]);
	return date + ' ' + time
}

$.ajaxSettings.traditional = true;
function sendAjaxReport(post, reason) {
	$.ajax({
		url : "/ajax/report/",
		type : "POST",
		data : {post: post, reason: reason, _xsrf: getCookie("_xsrf")},
		success : function(json) {
		},

		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};

function getCookie(c_name)
{
	if (document.cookie.length > 0)
	{
		c_start = document.cookie.indexOf(c_name + "=");
		if (c_start != -1)
		{
			c_start = c_start + c_name.length + 1;
			c_end = document.cookie.indexOf(";", c_start);
			if (c_end == -1) c_end = document.cookie.length;
			return unescape(document.cookie.substring(c_start,c_end));
		}
	}
	return "";
};
