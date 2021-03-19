$(document).ready(function(){
	$('body').on('click', '#popup-close', function(){
		$('.popup').fadeOut(400).delay(100).remove();
	});
});

function popUp(data) {
	document.querySelectorAll('.popup').forEach(el => el.remove())
	var pop = document.createElement('div');
	pop.classList.add('popup');
	pop,innerHTML = `<div id="popup-inner">${data}</div><button id="popup-close">X</button>`;
	document.getElementsByTagName('body')[0].appendChild(pop);
}
