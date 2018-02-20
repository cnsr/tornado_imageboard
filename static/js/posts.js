var window_focus = true;
var unread = 0;
var title;
var title_orig;
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
	title = window.document.title;
	title_orig = window.document.title;
	$(window).focus(function () {
		unread = 0;
		title = title_orig;
		changeFavicon("/static/favicon.png");
		window.document.title = title;		
		window_focus = true;
	}).blur(function () {
		window_focus = false;
	});
	$(document).on('change', '#spoiler_images', function(){
		let spoiler = $(this).is(':checked');
		toggleSpoiler(spoiler);
	});
	$(document).on('keydown', function(e) {
		let key = e.which;
		let t = $(e.target);
		let spoiler = $('#spoiler_images').is(':checked');
		switch (key) {
			case 66:
			case 98:
			{
				if (!t.is('input') && !t.is('textarea')) {
					toggleSpoiler(!spoiler);
					$('#spoiler_images').prop('checked', !spoiler);
				}
				break;
			}
			default:
				return;
		}
	});
	$(document).on('click', '.post-href', function() {
		var number = $(this).attr('href');
		var addition = '>>';
		if ($('textarea').val() != '') {addition = '\n>>'};		
		var new_val = $('textarea').val() + addition + number.substring(1, number.length) + '\n';
		$('textarea').val(new_val);
		setTimeout(function() {
			$('.add').find('#text-area').get(0).focus();
		}, 1);
		if (!$('.add').hasClass('drag')) {
			$('html,body').animate({
				scrollTop: $('.add').offset().top
			}, 1000);
			return false;
		}
	});
	if ($('.oppost').length) {
		$(".post-header").each(function(i) {
			++i;
			$(this).find(".post-number").text(i++);
		});
	} else {
		 $('.thread-outer').each(function() {
			var rgx = /(\d+)(, .+)?/ig;
			if ($(this).find('.ommited').length) {
				let str = $(this).find('.ommited').text();
				var i = parseInt(rgx.exec(str)[0]) + 1;
			} else {
				var i = 2;
			}
			$(this).find(".post-number").each(function() {
				$(this).text(i++);
			})
		 })
	}
	$('.date').each(function() {
		var localTime  = moment.utc($(this).text()).toDate();
		localTime = moment(localTime).format('DD-MM-YYYY HH:mm:ss');;
		$(this).text(localTime);
	});	
	refreshThread();
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
	});
	$('#getnew').on('click', function(e) {
		e.preventDefault();
		var latest = $($('.post').slice(-1)[0]).attr('id');
		var url = '/' + board + '/thread/' + thread + '/new/';
		getNewAjax(latest, url);
		$('#newremain').text('20');		
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
			 //background: 'white'
		});
		$('body').append(display);
		if ($('.to_die').is(':offscreen')) {
			 $(this).css('bottom', 0);
		}
	});
	$('body').on('click', '.report', function() {
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
	$(document).on('click', '.pin', function(){
		var id = $(this).attr('data-id');
		sendAjaxPin(id);
	})
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

function loadPost(dict) {
	var template = $('#template').html();
	Mustache.parse(template);
	var rendered = Mustache.render(template, dict);
	$('.posts').append(rendered);
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

function sendAjaxPin(post) {
	$.ajax({
		url : "/ajax/pin/",
		type : "POST",
		data : {post: post, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			popUp(json['status']);
		},

		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};


function getNewAjax(latest, url) {
	$.ajax({
		url : url,
		type : "POST",
		data : {latest:latest, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			$.each(json, function(index, obj) {
				obj['date'] = switchDate(obj['date']);
				obj['text'] = replaceText(obj['text']);
				loadPost(obj);
				if (window_focus === false) {
					unread++;
					title = "(" + unread + ") " + title_orig;
					changeFavicon("/static/favicon-unread.png");
    			}
			})
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

jQuery.expr.filters.offscreen = function(el) {
  var rect = el.getBoundingClientRect();
  return (
           (rect.x + rect.width) < 0 
             || (rect.y + rect.height) < 0
             || (rect.x > window.innerWidth || rect.y > window.innerHeight)
         );
};

function switchDate(date){
	var localTime  = moment.utc(date).toDate();
	return moment(localTime).format('DD-MM-YYYY HH:mm:ss');
}

function refreshThread() {
	$('#newremain').text('20');
	$('#getnew').trigger('click');
	let changer = setInterval(function(){
		let i = parseInt($('#newremain').text()) - 1;
		$('#newremain').text(i);
	}, 1000);
	setTimeout(function(){
		clearInterval(changer);
		refreshThread();
	}, 20000);
};

function changeFavicon(src) {
	var link = document.createElement('link'),
	oldLink = document.getElementById('dynamic-favicon');
	link.id = 'dynamic-favicon';
	link.rel = 'shortcut icon';
	link.href = src;
	if (oldLink) {
		document.head.removeChild(oldLink);
	}
	document.head.appendChild(link);
	window.document.title = title
}


function toggleSpoiler(spoiler) {
	$('.post-media').each(function() {
		if (!spoiler) {
			$(this).css('opacity', '');
		} else {
			$(this).css('opacity', '0.1');
		}
	})
}
