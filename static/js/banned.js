$(document).ready(function() {
	var today = new Date();
	var tomorrow = new Date(today.getTime() + (24 * 60 * 60 * 1000));
	tomorrow.setHours(0,0,0,0);
	$("#ban-expires").datepicker({
		minDate: tomorrow,
		dateFormat: 'dd-mm-yy'
	});
	$('.banform').draggable({
		containment: "window"	
	});
	$('#ban-never').change(function(){
		 $('.ban-expires-div').toggle();
	})
	$('.ban').on('click', function(){
		 $('.banform').css('display','inline-block');
		 $('#ban-post').val($(this).attr('data-id'));
	})
	$('#ban-submit').on('click', function(e) {
		e.preventDefault();
		var post = $('#ban-post').val();
		var ban = '';
		if ($('#ban-never').is(':checked')) {
			ban = 'Never';
		} else {
			ban = $('#ban-expires').val();
		}
		if ($('#ban-lock').is(':checked')) {
			 var lock = 'true';
		} else { var lock = 'false'; }
		var reason = $('#ban-reason').val();
		sendAjaxBan(post, ban, reason, lock);
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

