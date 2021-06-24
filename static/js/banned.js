var initX_bf, initY_bf, firstX_bf, firstY_bf;


const mouseDownBanForm = (e) => {
	console.log('banForm movement')
	e.preventDefault();
	let target = e.target;

	initX_bf = target.offsetLeft;
	initY_bf = target.offsetTop;

	firstX_bf = e.pageX;
	firstY_bf = e.pageY;

	target.addEventListener('mousemove', mouseMoveBanForm, false);

	window.addEventListener('mouseup', (event) => {
		target.removeEventListener('mouseMove', mouseMoveBanForm, false);
	})
}

const mouseMoveBanForm = (e) => {
	e.target.style.left = `${initX_bf + e.pageX - firstX_bf}px`;
	e.target.style.top = `${initY_bf + e.pageY - firstY_bf}px`;
}


$(document).ready(function() {
	[...document.getElementsByClassName('banform')].map(el => el.addEventListener('mousedown', mouseDownBanForm, false));

	$('#ban-never').change(function(){
		 $('.ban-expires-div').toggle();
	})
	$(document).on('click', '.ban', function(){
		$('.banform').css({'display':'inline-block', 'top': '25px', 'left': '60%'});
		$('#ban-post').val($(this).attr('data-id'));
		/* sets all box values to default */
		$('#ban-never').val('');
		$('#ban-lock').val('');
		$('#ban-expires').val('');
		$('#ban-reason').val('');		
	})
	$('#ban-submit').on('click', function(e) {
		e.preventDefault();
		var post = $('#ban-post').val();
		var ban;
		var lock;
		var rm = $('#ban-rm').is(':checked');
		if ($('#ban-never').is(':checked')) {
			ban = 'Never';
		} else {
			var today = new Date();
			let ban_total = 0;
			let ban_days = parseInt($('#ban-days').val());
			let ban_hours = parseInt($('#ban-hours').val());
			let ban_minutes = parseInt($('#ban-minutes').val());
			if (ban_days != 0) ban_total += ban_days * 24 * 60 * 60 * 1000;
			if (ban_hours != 0 ) ban_total += ban_hours * 60 * 60 * 1000;
			if (ban_minutes != 0 ) ban_total += ban_minutes * 60 * 1000;
			let _ban = (new Date(today.getTime() + ban_total)).toGMTString();
			// ban = moment(_ban).format('DD-MM-YYYY HH:mm:ss');
			ban = moment.utc(_ban)._i;
		}
		if ($('#ban-lock').is(':checked')) {
			 lock = 'true';
		} else { lock = 'false'; }
		var reason = $('#ban-reason').val();
		var banMessage = $('#ban-message').val();
		
		sendAjaxBan(post, ban, reason, banMessage, lock, rm);
		$('.banform').hide();
	})
	$('#ban-close').on('click', function() {
		$('.banform').hide();		 
	})
});

$.ajaxSettings.traditional = true;
function sendAjaxBan(post, date, reason, banMessage, lock, rm) {
	$.ajax({
		url : "/ajax/ban/",
		type : "POST",
		data : {post: post, date: date, reason: reason, ban_message: banMessage, lock: lock, rm: rm, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			$('#' + post).append(`<p class="banned">${banMessage ? banMessage : "User has been banned for this post"}</p>`);
			if (rm) $('#' + post).parent().remove();
			popUp('User has been banned');
		},

		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
			popUp('Failed to ban user');
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
