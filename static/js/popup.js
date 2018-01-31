$(document).ready(function(){
	$('body').on('click', '#popup-close', function(){
		$('.popup').fadeOut(400).delay(100).remove();
	});
});

function popUp(data) {
	$('.popup').remove();
	var pop = '<div class="popup"><div id="popup-inner">'+data+'</div><button id="popup-close">X</button></div>';
	$('body').append(pop);
	$('.popup').effect('shake', { times:1 }, 400);
}
