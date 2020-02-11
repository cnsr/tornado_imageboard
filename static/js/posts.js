var window_focus = true;
var unread = 0;
var title;
var title_orig;
var pin_id;

$(document).ready(function(){
	$('.file_remove').on('click', function(e) {
		e.preventDefault();
		$('#' + $(this).attr('data-id')).val(null).css('display','block');
		$(this).hide();
		$(this).next("br").remove();
	});
	$(document).on("dragstart", function(e) {
		if (e.target.nodeName.toUpperCase() == "IMG") {
			return false;
		}
	});
	if (localStorage.name != '' && localStorage.name != null) $('#username').val(localStorage.name);
	if (typeof localStorage.hidden == undefined || localStorage.hidden == '') localStorage.hidden = JSON.stringify([]);
	var hidden = JSON.parse(localStorage.hidden || null);
	if (!hidden) {
		localStorage.hidden = JSON.stringify([])
		hidden = [];
	}
	hidden.forEach(function(item, i , arr) {
		let th = $('#' + item);
		hideThread(th);
	});
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
	$(document).on('click', '.hide', function() { 
		let thread = $(this).attr('data-thread');
		hidden.push(thread);
		localStorage.hidden = JSON.stringify(hidden);
		hideThread($('#' + thread));
	});
	$(document).on('mouseenter', '.hidden-href', function() { 
		$('#' + $(this).attr('data-id')).children(':not(:first-child)').show();
	});
	$(document).on('mouseleave', '.hidden-href', function() { 
		$('#' + $(this).attr('data-id')).children(':not(:first-child)').hide();
	});
	$(document).on('click', '.hidden-href', function() {
		let id = $(this).attr('data-id');
		$('#' + id).children(':not(:first-child)').show();
		$(this).parent().remove();
		hidden.splice(hidden.indexOf(id), 1);
		localStorage.hidden = JSON.stringify(hidden);
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
			case 37:
			{
				if (!t.is('input') && !t.is('textarea')) {				
					if (e.ctrlKey && $('.modal').find('.modal-image').length) {
						$('#modalL').trigger('click');
					}
				};
				break;
			}
			case 39:
			{
				if (!t.is('input') && !t.is('textarea')) {				
					if (e.ctrlKey && $('.modal').find('.modal-image').length) {
					$('#modalR').trigger('click');
					}
				};
				break;
			}
			case 27:
			{
				$('.modal').empty();
				$('.modal-image').css('width', '0px').attr('top', 0).attr('left', 0);
				$('.modal-controls').hide();
			}
			default:
				return;
		}
	});
	$(document).on('click', '.post-href', function() {
		if ($('#text-area').length) {
			if (!$(this).hasClass('ignore')) {
				var number = $(this).attr('href');
				var addition = '>>';
				$('textarea').val($('textarea').val().trim());
				if ($('textarea').val() != '') {addition = '\n>>'};
				var new_val = $('textarea').val() + addition + number.substring(1, number.length) + '\n';
				$('textarea').val(new_val);
				setTimeout(function() {
					if ($('.add').length) $('#text-area').putCursorAtEnd();
				}, 1);
				if (!$('.add').hasClass('drag')) {
					if (!typeof $('.add').offset() === undefined) {
						$('html,body').animate({
							scrollTop: $('.add').offset().top
						}, 1000);
						return false;
					}
				}
			}
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
				var i = parseInt(rgx.exec(str)[0]) + 2;
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
	$('#bnr').on('click', function() {
		let to = $(this).attr('data-goto');
		window.location.replace(to);
	})
	$('body').on('mouseover', 'a.reply', function() {
		$('.to_die').removeClass('latest');
		let id = $(this).attr('href');
		let a = $(this);
		if ($(id).length) {
			var display = $(id).clone();
			if (display.is('.thread-outer')) {
				display = display.find('.thread');
			}
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
			display.addClass('latest');
			$('body').append(display);
			if ($('.to_die').is(':offscreen')) {
				 $(this).css('bottom', 0);
			}
		} else {
			getPost(id.slice(1), a);
		}
	});
	$('.text').each(function() {
		if ($(this).height()/2 > 100) {
			$(this).addClass('shortened');
			let unshort = '<span class="showmore">Show more</span>';
			$(this).after(unshort);
		}
	});
	$('body').on('click', '.showmore', function() {
		$(this).prev('.text').removeClass('shortened');
		$(this).remove();
	});
	$(document).on('click', '.seal', function() {
		var id = $(this).attr('data-id');
		sendAjaxSeal(id);
	})
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
	$('body').on('click', '#pin-close', function(){
		 $('#pin-selector').hide();
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
	$(document).on('click', '.pin_b', function(){
		pin_id = $(this).attr('data-id');
		$('#pin-selector').show();
	})
	$(document).on('click', '#pin-submit', function(){
		$('#pin-selector').hide();
		let selected_boards = new Array();
		$('.pinform').find('input:checkbox:checked').each(function() {
			selected_boards.push($(this).attr('name'));
		});
		sendAjaxPinThread(pin_id, selected_boards);
	})	
	$(document).on('click', '.infinify', function(){
		var id = $(this).attr('data-id');
		sendAjaxInfinify(id);
	})	
	$(document).on('click', '.admin-lock', function(){
		var id = $(this).attr('data-id');
		sendAjaxLock(id);
	})
	$(document).on('click', '.admin-move', function(){
		$('#select-list').remove();
		var id = $(this).attr('data-id');
		let boards = $('.boards-list a');
		let div = $('<div id="move-div">');
		let list = $('<select id="move-list">');
		for (i=0;i<boards.length;i++) {
			let href = $(boards[i]).attr('href').split('/').pop();
			if (href != board) {
				list.append($('<option>', {
					value: href,
					text: '/' + href + '/',
					class: 'move-option',
					id: href + '-' + id
				}))
			}
		}
		div.append(list);		
		div.append($('<button id="move-select">move</button><br />'));
		div.append($('<button id="move-cancel">cancel</button>'));
		$('body').append(div);
	});
	$('body').on('click', '#move-cancel', function() {
		$('#move-div').remove();
	})	
	$('body').on('click', '#move-select', function() {
		let s = $('#move-list').find(':selected');
		$('#move-div').remove();
		sendAjaxMove(s.attr('id'));
	})
	$('body').on('mouseover', '.to_die', function(e) {
        $(this).addClass('is-hover');
    });
	$('body').on('mouseleave', '.to_die', function(e) {
        $(this).removeClass('is-hover');
		setTimeout(function() {
			if (!$('.to_die:hover').length && !$('a.reply:hover').length) {
				$('.to_die').remove();
			}
		}, 1250);		
    });	
	$('body').on('mouseleave', 'a.reply', function(e) {
		var to_rm = '#' + $(this).text().slice(2) + '.to_die';
		setTimeout(function() {
			if (!$(to_rm).hasClass('is-hover')) {
				$(to_rm + '.latest').remove();
			}
		}, 250);
	});
});

function loadPost(dict) {
	var template = $('#template').html();
	Mustache.parse(template);
	for (var i = 0; i < dict['files'].length; i++) {
		switch (dict['files'][i]['filetype']) {
			case 'image':
				dict['files'][i]['image'] = true;
				break;
			case 'video':
				dict['files'][i]['video'] = true;
				break;
			case 'audio':
				dict['files'][i]['audio'] = true;
				break;
			default: break;
		};
	}
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

const sendAjaxSeal = (id) => {
	$.ajax({
		url : '/ajax/seal',
		type: 'POST',
		data: {post: id, _xsrf: getCookie("_xsrf")},
		success: (json) => {
			popUp('Sealed, refresh cuz im too lazy to code this in')
		},
		error: (err) => {
			console.log(err)
			popUp('Error wtf tell yaro to fix')
		}
	})
}

function sendAjaxMove(post) {
	$.ajax({
		url : "/ajax/move/",
		type : "POST",
		data : {post: post, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			if (json.status == 'Moved') {
				popUp('Thread has been moved!');
				let mv = post.split('-');
				let to = '/' + mv[0] + '/thread/' + mv[1];
				setTimeout(function() {
					window.location.replace(to);
				}, 2000);
			}
		},
		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};


function getPost(post, a) {
	$.ajax({
		url : "/ajax/get/",
		type : "POST",
		data : {post: post, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			if ('post' in json) {
				var post = json['post'];
				post['date'] = switchDate(post['date']);
				post['text'] = replaceText(post['text']);
				var template = $('#template').html();
				Mustache.parse(template);
				for (var i = 0; i < post['files'].length; i++) {
					switch (post['files'][i]['filetype']) {
						case 'image':
							post['files'][i]['image'] = true;
							break;
						case 'video':
							post['files'][i]['video'] = true;
							break;
						case 'audio':
							post['files'][i]['audio'] = true;
							break;
						default: break;
					};
				}

				var rendered = Mustache.render(template, post);
				var display = $('<div/>').html(rendered).contents().find('.post');
				display.toggleClass('to_die', true);
				display.css({
					 display:'inline',
					 position: 'absolute',
					 top: a.offset().top - a.height()/2,
					 left: a.offset().left + a.width(),
					 border: '1px black solid',
					 padding: '6px 3px',
					 zIndex: 1000,
				});
				display.addClass('latest');
				display.find('.report').remove();
				$('body').append(display);
				if ($('.to_die').is(':offscreen')) {
					 $(this).css('bottom', 0);
				}
			} else {
				popUp(json['status']);
				return;
			}
		},

		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};

function sendAjaxInfinify(post) {
	$.ajax({
		url : "/ajax/infinify/",
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

function sendAjaxPinThread(post, selected_boards) {
	$.ajax({
		url : "/ajax/pin_thread/",
		type : "POST",
		data : {post: post, _xsrf: getCookie("_xsrf"), boards: JSON.stringify(selected_boards)},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			popUp(json['status']);
		},

		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};


function sendAjaxLock(post) {
	$.ajax({
		url : "/ajax/lock/",
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
				if (!$('#' + obj['count']).length) {
					loadPost(obj);
					if (window_focus === false) {
						unread++;
						title = "(" + unread + ") " + title_orig;
						changeFavicon("/static/favicon-unread.png");
					}
				}
			})
		},
		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};

$.ajaxSettings.traditional = true;
function sendAjaxUpvote(id, action) {
	$.ajax({
		url : "/ajax/upvote/",
		type : "POST",
		data : {post: id, _xsrf: getCookie("_xsrf"), action: action},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			if (json.status == 'voted') {
				console.log('voted');
			} else {
				console.log('didnt vote and you are white')
			}
		},
		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};


$.ajaxSettings.traditional = true;
function sendAjaxDel(id) {
	$.ajax({
		url : "/ajax/delete/",
		type : "POST",
		data : {post: id, _xsrf: getCookie("_xsrf"), password: localStorage.pass},
		success : function(json) {
			var json = jQuery.parseJSON(json);
			if (json.status == 'deleted') {
				popUp('Deleted');
				$('#' + id).fadeOut('slow');
			} else {
				popUp('Passwords do not match');
			}
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
		if (!$(this).parents().hasClass('.modal')) {
			if (!spoiler) {
				$(this).css('opacity', '');
			} else {
				$(this).css('opacity', '0.1');
			}
		}
	})
}

function hideThread(thread) {
	th = thread.find('.thread');
	let th_id = thread.attr('id');
	let th_text = th.find('.psubject').text();
	if (!th_text || /\S/.test(th_text)) {
		th_text = th.find('.text').text();
	}
	if (!th_text || /\S/.test(th_text)) {
		th_text = th.find('.filedata-p').text();
	}
	if (!th_text || /\S/.test(th_text)) {
		th_text = '>>' + th_id;
	}
	th_text = th_text.length > 50 ? th_text.substring(0, 50) + '...' : th_text;
	let replacement = '<div class="thread-header hidden">Hidden thread: <a class="hidden-href" data-id="'+
	+ th_id + '">>>' + th_id + '</a> (' + th_text + ')</div>';
	thread.children().hide();
	thread.prepend(replacement);
}

String.prototype.trim = function() {
  return this.replace(/^\s+|\s+$/g, "");
}

jQuery.fn.putCursorAtEnd = function() {

  return this.each(function() {

    $(this).focus()
    if (this.setSelectionRange) {
      var len = $(this).val().length * 2;

      this.setSelectionRange(len, len);

    } else {
      $(this).val($(this).val());
    }
  });

};;
