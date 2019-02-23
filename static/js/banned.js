$(document).ready(function() {
	$('.banform').draggable({
		containment: "window"	
	});
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
		var ban = '';
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
			//ban = moment(_ban).format('DD-MM-YYYY HH:mm:ss');
			ban = moment.utc(_ban)._i;
		}
		if ($('#ban-lock').is(':checked')) {
			 var lock = 'true';
		} else { var lock = 'false'; }
		var reason = $('#ban-reason').val();
		sendAjaxBan(post, ban, reason, lock);
		popUp('User has been banned');
		$('.banform').hide();
	})
	$('#ban-close').on('click', function() {
		$('.banform').hide();		 
	})
});

$.ajaxSettings.traditional = true;
function sendAjaxBan(post, date, reason, lock) {
	$.ajax({
		url : "/ajax/ban/",
		type : "POST",
		data : {post: post, date: date, reason: reason, lock: lock, _xsrf: getCookie("_xsrf")},
		success : function(json) {
			$('#' + post).append('<p class="banned">User has been banned for this post</p>');
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
