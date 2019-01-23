var default_theme = 'brutalism.css';

$(document).ready(function(){
	$('[value="' + localStorage.theme + '"]').attr('selected', true);	
	$('#themes').change(function () {
		get_css($(this).val());
		localStorage.theme = $(this).val().replace("null", default_theme);
	});
	$('#settings-btn').on('click', function() {
		$('#settings-menu').toggle();
	});
	$('#settings-hide').on('click', function() {
		$('#settings-menu').hide();
	})
	$("#top").click(function() {
		$("html, body").animate({ scrollTop: 0 }, "fast");
		return false;
	});
	$("#btm").click(function() {
		$("html, body").animate({ scrollTop: document.body.scrollHeight }, "fast");
		return false;
	});

});

function get_theme() {
	if (typeof localStorage.theme != 'undefined') {
		get_css(localStorage.theme);
		$('[value="' + localStorage.theme + '"]').attr('selected', true);
	} else {
		get_css(default_theme);
		localStorage.theme = default_theme;		
		$('[value="' + default_theme + '"]').attr('selected', true);
	};
}

function get_css(file) {
    "use strict";
    if ($('#_css')) {
        $('#_css').remove();
    }
    var head = document.getElementsByTagName('head')[0];
    var link = document.createElement('link');
    link.id = '_css';
    link.rel = 'stylesheet';
    link.type = 'text/css';
    link.href = '/static/' + file;
    link.media = 'all';
    $('head').append(link);
}
