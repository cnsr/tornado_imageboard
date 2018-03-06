$(document).ready(function() {
	if (typeof localStorage.pass === 'undefined') {
		localStorage.pass = Math.random().toString(36).substring(7);
		$('#setpass').val(localStorage.pass);
	};
	setPass(localStorage.pass);
	$('#setpass').on('change', function() {
		setPass($(this).val());
	});
	$('#setpasslbl').hover(function () {
		$('#setpass').attr('type', 'text');
	}, function () {
		$('#setpass').attr('type', 'password');
	});
	$(document).on('click', '.del-post', function(){
		var id = $(this).attr('data-id');
		sendAjaxDel(id);
	});
})

function setPass(v) {
	$('#setpass').val(v);	
	localStorage.pass = v;
	$('#newpostpass').val(v);
}

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
			} else {
				popUp('Passwords do not match');
			}
		},
		error : function(xhr,errmsg,err) {
			console.log(xhr.status + ": " + xhr.responseText);
		}
	});
};
