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
	$('#setpass').on('focus', function() {
		$(this).attr('type','text');
		$(this).attr('readonly',false);
	})
	$('#setpass').on('blur', function() {
		$(this).attr('type','password');
		$(this).attr('readonly',true);
	})
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

